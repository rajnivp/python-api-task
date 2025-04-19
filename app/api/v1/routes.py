from typing import List, Dict, Any, Optional, Union

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.auth import verify_token
from app.core.config import settings, bts
from app.core.logger import logger
from app.tasks.background_tasks import process_sentiment_and_stake, store_dividends_batch_task

router = APIRouter()

r: Redis = redis.from_url(settings.redis_url)


@router.get("/tao_dividends", dependencies=[Depends(verify_token)])
async def get_tao_dividends(
        netuid: int = 0,
        hotkey: str = '',
        trade: bool = False
) -> Dict[str, Union[bool, List[Dict[str, Any]]]]:
    netuids_and_hotkeys: Dict[int, List[str]] = {}
    dividends = dict()
    logger.info(f'Params received, netuid:{netuid}, hotkey: {hotkey}, trade:{trade}')
    
    if not netuid:
        logger.info(f'No netuid provided, fetching all subnet netuids...')
        all_netuids: List[int] = await bts.get_all_netuids()
        logger.info(f'All subnet netuids: {all_netuids}, fetching hotkeys for each netuid...')
        for netuid in all_netuids:
            netuids_and_hotkeys[netuid] = bts.get_hotkeys_for_netuid(netuid=netuid)
            dividends = bts.get_dividends_for_all_hot_keys(netuid=netuid)
            logger.info(f'Hotkeys for netuid {netuid}: {netuids_and_hotkeys[netuid]}')
    elif not netuids_and_hotkeys and not hotkey:
        logger.info(f'Hotkey not provided, getting all hotkeys for netuid {netuid}')
        netuids_and_hotkeys[netuid] = bts.get_hotkeys_for_netuid(netuid=netuid)
        logger.info(f'Hotkeys for netuid {netuid}: {netuids_and_hotkeys[netuid]}')
        dividends = bts.get_dividends_for_all_hot_keys(netuid=netuid)
    else:
        netuids_and_hotkeys[netuid] = [hotkey]

    dividends = dict(dividends)

    response: List[Dict[str, Any]] = []
    dividends_to_store: List[Dict[str, Any]] = []

    for netuid, hotkeys in netuids_and_hotkeys.items():
        for hotkey in hotkeys:
            cache_key: str = f"dividends:{netuid}:{hotkey}"
            cached: Optional[bytes] = await r.get(cache_key)
            logger.info(f'Cached: {cached} for cache_key: {cache_key}')
            
            if cached:
                result: str = cached.decode()
            else:
                if not dividends:
                    dividends = bts.get_dividends_for_all_hot_keys(netuid=netuid)
                result: Optional[str] = dict(dividends).get(hotkey)

                await r.setex(name=cache_key, time=settings.CACHE_EXPIRATION, value=result)
            logger.info(f'Dividend for {cache_key}: {result}, cached: {cached}')

            # Collect dividend data for batch storage
            try:
                dividend_amount: float = float(result) if result else 0.0
                dividends_to_store.append({
                    "netuid": netuid,
                    "hotkey": hotkey,
                    "amount": dividend_amount
                })
            except Exception as e:
                logger.error(f"Error processing dividend for netuid {netuid}, hotkey {hotkey}: {str(e)}", exc_info=True)

            response.append({
                'netuid': netuid,
                'hotkey': hotkey,
                'dividend': result,
                'stake_tx_triggered': trade,
                'cached': cached
            })

    # Store all dividends in a batch using the generic store function
    if dividends_to_store:
        try:
            task = store_dividends_batch_task.delay(dividends_to_store)
            logger.info(f"Triggered batch dividend storage task with task_id: {task.id} for {len(dividends_to_store)} "
                        f"records")
        except Exception as e:
            logger.error(f"Error triggering batch dividend storage task: {str(e)}", exc_info=True)

    # Start the workflow for sentiment analysis and staking
    if trade:
        process_sentiment_and_stake.delay(netuid, hotkey)
        logger.info(f"Started sentiment analysis and staking workflow for netuid {netuid}")

    return {'success': True, 'result': response}
