"""
API routes for the TAO Dividend Sentiment Service.

This module defines the FastAPI router and endpoints for handling
dividend data, sentiment analysis, and staking operations.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Union

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.auth import verify_token
from app.core.config import settings, bts
from app.core.logger import logger
from app.tasks.background_tasks import process_sentiment_and_stake, store_dividends_batch_task
from app.db.models import Dividend, SentimentStakeOperation


router = APIRouter()

redis_instance: Redis = redis.from_url(settings.redis_url)

CACHE_EXPIRATION = settings.CACHE_EXPIRATION


def get_hotkeys_and_dividends_for_netuid(netuid: int) -> Union[Dict[int, Dict[str, float]], None]:
    """
    Get hotkeys and dividends for a specific network UID.
    
    Args:
        netuid (int): Network UID to query
        
    Returns:
        Union[Dict[int, Dict[str, float]], None]: Dictionary mapping netuid to hotkey-dividend pairs,
                                                 or None if an error occurs
    """
    try:
        dividends = bts.get_dividends_for_all_hot_keys(netuid=netuid)
        return {netuid: dict(dividends)}
    except Exception as e:
        logger.error(f"Error in getting dividends and hotkeys for netuid {netuid}: {str(e)}", exc_info=True)


def get_hotkeys_and_dividends_for_all_netuids_threadpool(netuids: List[int]) -> Dict[int, Dict[str, float]]:
    """
    Get hotkeys and dividends for multiple network UIDs using a thread pool.
    
    Args:
        netuids (List[int]): List of network UIDs to query
        
    Returns:
        Dict[int, Dict[str, float]]: Dictionary mapping each netuid to its hotkey-dividend pairs
    """
    with ThreadPoolExecutor(max_workers=10) as executor:
        res = executor.map(get_hotkeys_and_dividends_for_netuid, netuids)
    dividends_data = dict()
    for r in res:
        if r is not None:
            dividends_data.update(r)
    return dividends_data


@router.get('/get_all_dividends_stakes_data', dependencies=[Depends(verify_token)])
async def get_all_dividends_stakes_data():
    """
    Get all dividend and staking operation data from the database.
    
    Returns:
        Dict: Response containing dividend and sentiment data rows
    """
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            result = await session.execute(select(Dividend))
            rows = result.scalars().all()
            dividend_rows = [
                {key: value for key, value in row.__dict__.items() if key != '_sa_instance_state'}
                for row in rows
            ]
            result = await session.execute(select(SentimentStakeOperation))
            rows = result.scalars().all()
            sentiment_data_rows = [
                {key: value for key, value in row.__dict__.items() if key != '_sa_instance_state'}
                for row in rows
            ]
            return {'success': True, 'dividends': dividend_rows, 'sentiment_data': sentiment_data_rows}
    except Exception as e:
        logger.error(f"Error in get_tao_dividends: {str(e)}", exc_info=True)
        return {'success': False, 'msg': str(e)}


@router.get("/tao_dividends", dependencies=[Depends(verify_token)])
async def get_tao_dividends(
        netuid: int = None,
        hotkey: str = '',
        trade: bool = False
) -> Dict[str, Union[bool, str, List[Dict[str, Any]]]]:
    """
    Get TAO dividends for specified network UID and hotkey.
    
    Args:
        netuid (int, optional): Network UID to query
        hotkey (str, optional): Hotkey to query
        trade (bool, optional): Whether to trigger sentiment analysis and staking
        
    Returns:
        Dict[str, Union[bool, str, List[Dict[str, Any]]]]: Response containing dividend data
    """
    logger.info(f'Params received, netuid:{netuid}, hotkey: {hotkey}, trade:{trade}')
    try:
        netuid_hotkeys_dividends = dict()
        response_items = []
        dividends_to_store = []
        cached = False
        msg = ''
        staking_netuid = netuid if netuid is not None else settings.wallet_netuid
        staking_hotkey = hotkey or settings.wallet_hotkey

        # Not caching dividends when netuid or hotkey is ommited, because to get data from redis cache
        # we need to have netuid and hotkey so that's why in those two cases we're getting data from bittensor
        # and as they send data for all hotkeys in single response it's quick

        if netuid is None:  # Fetching dividends also as hotkeys and dividends are available in same response
            # Get all netuid and their hotkeys and their dividends
            logger.info('No netuid provided, fetching all subnet netuids...')
            try:
                all_netuids = await bts.get_all_netuids()
            except Exception as e:
                logger.error(f"Error in getting all netuids: {str(e)}", exc_info=True)
                all_netuids = []
            all_netuids = all_netuids
            logger.info(f'All subnet netuids: {all_netuids}, fetching hotkeys and dividends for all')
            netuid_hotkeys_dividends = get_hotkeys_and_dividends_for_all_netuids_threadpool(netuids=all_netuids)
            if not netuid_hotkeys_dividends:
                msg = f'Dividends data not found for netuids: {all_netuids}'

        elif not hotkey:  # Fetching dividends also as hotkeys and dividends are available in same response
            # Get hotkeys and their dividends for specific netuid
            logger.info(f'Hotkey not provided, getting all hotkeys and their dividends for netuid {netuid}')
            netuid_hotkeys_dividends = get_hotkeys_and_dividends_for_netuid(netuid)
            if not netuid_hotkeys_dividends:
                msg = f'Dividends data not found for hotkeys for netuid: {netuid}'

        else:  # Checking redis cache and if dividend is not in redis cache then only fetching from bittensor
            # Single hotkey case
            cache_key = f'{netuid}:{hotkey}'
            cached = await redis_instance.get(cache_key)
            if cached:
                cached = True
                netuid_hotkeys_dividends = {netuid: {hotkey: cached}}
            else:
                cached = False
                res = get_hotkeys_and_dividends_for_netuid(netuid)
                if not res:
                    msg = f'No data found for netuid: {netuid}'
                    logger.error(msg)
                else:
                    dividend = res.get(netuid, {}).get(hotkey, {})
                    if not dividend:
                        msg = f'Dividend data not found for netuid: {netuid} and hotkey: {hotkey}'
                        logger.error(msg)
                    netuid_hotkeys_dividends = {netuid: {hotkey: dividend}}
                    await redis_instance.setex(cache_key, CACHE_EXPIRATION, dividend)

        if not netuid_hotkeys_dividends:
            logger.info(msg)
            return {'success': False, 'msg': msg, 'result': response_items}

        logger.info(f'Netuids, hotkeys and dividends: {netuid_hotkeys_dividends}')

        for netuid, result in netuid_hotkeys_dividends.items():
            for hotkey, dividend in result.items():
                dividends_to_store.append({
                    "netuid": netuid,
                    "hotkey": hotkey,
                    "amount": dividend
                })

                response_items.append({
                    'netuid': netuid,
                    'hotkey': hotkey,
                    'dividend': dividend,
                    'stake_tx_triggered': trade,
                    'cached': cached
                })

        # Store dividends in batch
        try:
            task = store_dividends_batch_task.delay(dividends_to_store)
            logger.info(f"Triggered batch dividend storage task with task_id: {task.id} for "
                       f"{len(dividends_to_store)} records")
        except Exception as e:
            logger.error(f"Error triggering batch dividend storage task: {str(e)}", exc_info=True)

        # Start sentiment analysis and staking if requested
        if trade:
            try:
                process_sentiment_and_stake.delay(staking_netuid, staking_hotkey)
                logger.info(f"Started sentiment analysis and staking workflow for netuid {staking_netuid}")
            except Exception as e:
                logger.error(f"Error triggering staking task: {str(e)}", exc_info=True)

        return {'success': True, 'result': response_items}
    except Exception as e:
        logger.error(f"Error in get_tao_dividends: {str(e)}", exc_info=True)
        return {'success': False, 'msg': str(e), 'result': []}
