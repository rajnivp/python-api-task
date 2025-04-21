import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from app.core.celery_app import celery_app
from app.db.database import create_async_engine, sessionmaker, settings, AsyncSession
from app.db.models import Dividend
from app.services.chutes import get_sentiment
from app.services.datura import get_tweets
from app.services.staking import submit_stake_adjustment

logger = logging.getLogger(__name__)

ResultType = Dict[str, Union[bool, str]]


@celery_app.task
def store_dividends_batch_task(
        dividends_data: List[Dict[str, Any]],
        timestamp_field: Optional[str] = 'timestamp') -> ResultType:
    async def store_using_async_session():
        # Create a database session
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            try:
                # Create model objects
                dividend_objects: List[Dividend] = []
                for data in dividends_data:
                    # Create a copy of the data to avoid modifying the original
                    obj_data: Dict[str, Any] = data.copy()

                    # Add timestamp if specified
                    if timestamp_field and timestamp_field not in obj_data:
                        obj_data[timestamp_field] = datetime.utcnow()

                    dividend_objects.append(Dividend(**obj_data))

                # Add all objects to the session
                db.add_all(dividend_objects)
                await db.commit()

                logger.info(f"Successfully stored {len(dividend_objects)} dividend records in batch")
            except Exception as e:
                await db.rollback()
                logger.error(f"Error storing dividends batch: {str(e)}", exc_info=True)

    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result: ResultType = loop.run_until_complete(store_using_async_session())
    loop.close()
    return result


@celery_app.task
def process_sentiment_and_stake(netuid: int, hotkey: str) -> None:
    """
    Process sentiment analysis and stake in a chain of tasks.
    
    Args:
        netuid: The network UID
        hotkey: The hotkey for staking
    """
    tweets: List[Dict[str, Any]] = get_tweets(prompt=f'Bittensor')
    if not tweets:
        logger.error(f'Error fetching tweets, abandoning stake/unstake operation')
        return
    sentiment_score: float = asyncio.run(get_sentiment(data=tweets))
    if sentiment_score is None:
        logger.error(f'Error fetching sentiment score, abandoning stake/unstake operation')
        return
    if not -100 <= sentiment_score <= 100:
        logger.error(f'Invalid sentiment score extracted: {sentiment_score}, abandoning stake/unstake operation')
        return
    submit_stake_adjustment(sentiment_score=sentiment_score, netuid=netuid, hotkey=hotkey)
