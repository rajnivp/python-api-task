"""
Background tasks for the TAO Dividend Sentiment Service.

This module defines Celery tasks for handling asynchronous operations such as
storing dividend data in batches and processing sentiment analysis and staking
operations. These tasks run in the background to avoid blocking the main application.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.celery_app import celery_app
from app.db.database import create_async_engine, sessionmaker, settings, AsyncSession
from app.db.models import Dividend
from app.services.chutes import get_sentiment
from app.services.datura import get_tweets
from app.services.staking import submit_stake_adjustment

logger = logging.getLogger(__name__)


def run_async(coroutine):
    """
    Helper function to run an async coroutine from a synchronous context.
    
    This function safely handles running async code in both sync and async contexts,
    avoiding the need to manually create and manage event loops.
    
    Args:
        coroutine: The async coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # If no loop is running, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()
    else:
        # If a loop is already running, use it
        return asyncio.ensure_future(coroutine)


@celery_app.task
def store_dividends_batch_task(
        dividends_data: List[Dict[str, Any]],
        timestamp_field: Optional[str] = 'timestamp'):
    """
    Store multiple dividend records in the database in a single batch operation.
    
    Args:
        dividends_data (List[Dict[str, Any]]): List of dividend records to store
        timestamp_field (Optional[str]): Name of the timestamp field, defaults to 'timestamp'
        
    The function creates an async database session and stores all dividend records
    in a single transaction. If any error occurs, the transaction is rolled back.
    """

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

    # Use the helper function to run the async database operation
    run_async(store_using_async_session())


@celery_app.task
def process_sentiment_and_stake(netuid: int, hotkey: str) -> None:
    """
    Process sentiment analysis and stake in a chain of tasks.
    
    This function performs the following steps:
    1. Fetches tweets related to the specified network UID
    2. Analyzes sentiment of the tweets
    3. Submits a stake adjustment based on the sentiment score
    
    Args:
        netuid (int): The network UID to analyze and stake
        hotkey (str): The hotkey to use for staking
        
    The function will log errors and abort the operation if any step fails.
    """
    tweets: List[Dict[str, Any]] = get_tweets(prompt=f'Bittensor netuid {netuid}')
    if not tweets:
        logger.error(f'Error fetching tweets, abandoning stake/unstake operation')
        return
    
    # Use the helper function to run the async sentiment analysis
    sentiment_score: float = run_async(get_sentiment(data=tweets))
    
    if sentiment_score is None:
        logger.error(f'Error fetching sentiment score, abandoning stake/unstake operation')
        return
    if not -100 <= sentiment_score <= 100:
        logger.error(f'Invalid sentiment score extracted: {sentiment_score}, abandoning stake/unstake operation')
        return
    submit_stake_adjustment(sentiment_score=sentiment_score, netuid=netuid, hotkey=hotkey)
