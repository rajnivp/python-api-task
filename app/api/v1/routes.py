import asyncio
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.auth import verify_token
from app.core.config import settings, bts
from app.core.logger import logger
from app.tasks.background_tasks import process_sentiment_and_stake, store_dividends_batch_task

router = APIRouter()

r: Redis = redis.from_url(settings.redis_url)

# Cache keys
NETUID_HOTKEYS_CACHE_KEY = "netuid_hotkeys_cache"
CACHE_EXPIRATION = settings.CACHE_EXPIRATION

# Create a thread pool for CPU-bound operations
thread_pool = ThreadPoolExecutor(max_workers=10)


async def get_cached_netuid_hotkeys() -> Optional[Dict[int, List[str]]]:
    """Get netuid and hotkeys from cache if available."""
    cached = await r.get(NETUID_HOTKEYS_CACHE_KEY)
    if cached:
        return json.loads(cached.decode())
    return None


async def cache_netuid_hotkeys(netuid_hotkeys: Dict[int, List[str]]):
    """Cache netuid and hotkeys with expiration."""
    await r.setex(
        NETUID_HOTKEYS_CACHE_KEY,
        CACHE_EXPIRATION,
        json.dumps(netuid_hotkeys)
    )


def get_hotkeys_for_netuid_sync(netuid: int) -> List[str]:
    """Synchronous function to get hotkeys for a netuid."""
    return bts.get_hotkeys_for_netuid(netuid=netuid)


async def get_netuid_hotkeys_with_threadpool(netuids: List[int]) -> Dict[int, List[str]]:
    """Get hotkeys for multiple netuids using ThreadPool."""
    loop = asyncio.get_event_loop()
    
    # Create tasks for each netuid
    tasks = [
        loop.run_in_executor(thread_pool, get_hotkeys_for_netuid_sync, netuid)
        for netuid in netuids
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    
    # Combine results
    return {netuid: hotkeys for netuid, hotkeys in zip(netuids, results)}


async def get_dividends_for_hotkey(netuid: int, hotkey: str) -> Tuple[bool, float]:
    """Get dividend for a specific hotkey with caching."""
    cache_key = f"dividends:{netuid}:{hotkey}"
    cached = await r.get(cache_key)
    
    if cached:
        return True, cached.decode()
    
    # Use thread pool for CPU-bound operation
    loop = asyncio.get_event_loop()
    dividends = await loop.run_in_executor(
        thread_pool, 
        lambda: bts.get_dividends_for_all_hot_keys(netuid=netuid)
    )
    
    result = dict(dividends).get(hotkey)
    
    if result:
        await r.setex(cache_key, CACHE_EXPIRATION, result)
    
    return False, result


async def process_hotkey_batch(netuid: int, hotkeys: List[str], trade: bool) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process a batch of hotkeys for a specific netuid."""
    response_items = []
    dividends_to_store = []
    
    # Get dividends for all hotkeys in parallel
    dividend_tasks = [get_dividends_for_hotkey(netuid, hotkey) for hotkey in hotkeys]
    dividend_results = await asyncio.gather(*dividend_tasks)
    
    for hotkey, result in zip(hotkeys, dividend_results):
        try:
            dividend_amount = float(result[1]) if result[1] else 0.0
            dividends_to_store.append({
                "netuid": netuid,
                "hotkey": hotkey,
                "amount": dividend_amount
            })
            
            response_items.append({
                'netuid': netuid,
                'hotkey': hotkey,
                'dividend': result,
                'stake_tx_triggered': trade,
                'cached': result[0]
            })
        except Exception as e:
            logger.error(f"Error processing dividend for netuid {netuid}, hotkey {hotkey}: {str(e)}", exc_info=True)
    
    return response_items, dividends_to_store


@router.get("/tao_dividends", dependencies=[Depends(verify_token)])
async def get_tao_dividends(
        netuid: int = 0,
        hotkey: str = '',
        trade: bool = False
) -> Dict[str, Union[bool, List[Dict[str, Any]]]]:
    logger.info(f'Params received, netuid:{netuid}, hotkey: {hotkey}, trade:{trade}')
    
    # Initialize response containers
    all_response_items = []
    all_dividends_to_store = []
    
    try:
        if not netuid:
            # Try to get netuid_hotkeys from cache first
            netuid_hotkeys = await get_cached_netuid_hotkeys()
            
            if not netuid_hotkeys:
                # If not in cache, fetch all netuids and their hotkeys using ThreadPool
                logger.info('No netuid provided, fetching all subnet netuids...')
                all_netuids = await bts.get_all_netuids()
                logger.info(f'All subnet netuids: {all_netuids}')
                
                # Use ThreadPool for CPU-bound operations
                netuid_hotkeys = await get_netuid_hotkeys_with_threadpool(all_netuids)
                await cache_netuid_hotkeys(netuid_hotkeys)
        elif not hotkey:
            # Get hotkeys for specific netuid using ThreadPool
            logger.info(f'Hotkey not provided, getting all hotkeys for netuid {netuid}')
            loop = asyncio.get_event_loop()
            hotkeys = await loop.run_in_executor(thread_pool, get_hotkeys_for_netuid_sync, netuid)
            netuid_hotkeys = {netuid: hotkeys}
        else:
            # Single hotkey case
            netuid_hotkeys = {netuid: [hotkey]}
        
        # Process each netuid's hotkeys in parallel
        tasks = [
            process_hotkey_batch(netuid, hotkeys, trade)
            for netuid, hotkeys in netuid_hotkeys.items()
        ]
        batch_results = await asyncio.gather(*tasks)
        
        # Collect results from all batches
        for response_items, dividends_to_store in batch_results:
            all_response_items.extend(response_items)
            all_dividends_to_store.extend(dividends_to_store)
        
        # Store dividends in batch
        if all_dividends_to_store:
            try:
                task = store_dividends_batch_task.delay(all_dividends_to_store)
                logger.info(f"Triggered batch dividend storage task with task_id: {task.id} for "
                            f"{len(all_dividends_to_store)} records")
            except Exception as e:
                logger.error(f"Error triggering batch dividend storage task: {str(e)}", exc_info=True)
        
        # Start sentiment analysis and staking if requested
        if trade:
            process_sentiment_and_stake.delay(netuid, hotkey)
            logger.info(f"Started sentiment analysis and staking workflow for netuid {netuid}")
        
        return {'success': True, 'result': all_response_items}
        
    except Exception as e:
        logger.error(f"Error in get_tao_dividends: {str(e)}", exc_info=True)
        return {'success': False, 'result': [], 'error': str(e)}
