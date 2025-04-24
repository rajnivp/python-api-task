"""
Staking service for the TAO Dividend Sentiment Service.

This module provides functionality for managing staking operations based on
sentiment analysis scores. It handles both staking and unstaking operations
on the Bittensor network and records these operations in the database.
"""

import asyncio
from typing import Dict, Any, Optional

from bittensor_cli.cli import Balance

from app.core.config import bts
from app.core.logger import logger
from app.db.database import create_async_engine, sessionmaker, settings, AsyncSession
from app.db.models import SentimentStakeOperation


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


def submit_stake_adjustment(
        sentiment_score: Optional[float],
        netuid: int,
        hotkey: str
) -> None:
    """
    Submit a stake adjustment based on sentiment score.
    
    This function performs the following operations:
    1. Calculates stake amount based on sentiment score (0.1 * score)
    2. For positive scores: stakes the calculated amount
    3. For negative scores: unstakes the absolute value of the calculated amount
    4. Records the operation in the database
    
    Args:
        sentiment_score (Optional[float]): Sentiment score between -100 and 100
        netuid (int): Network UID for the stake operation
        hotkey (str): Hotkey to stake/unstake
        
    The function will log errors and record failed operations in the database.
    If the sentiment score is 0, no stake adjustment is performed.
    """
    amount = 0.1 * sentiment_score
    success = False
    
    if sentiment_score > 0:
        operation = 'stake'
        try:
            success = run_async(bts.add_stake(
                wallet=bts.wallet, 
                netuid=netuid,
                amount=Balance.from_tao(amount=amount), 
                hotkey_ss58=hotkey
            ))
            logger.info(success)
        except Exception as e:
            logger.error(f"Error staking amount: {amount}: {str(e)}", exc_info=True)
            success = False

    elif sentiment_score < 0:
        operation = 'unstake'
        try:
            success = run_async(bts.unstake(
                wallet=bts.wallet, 
                netuid=netuid,
                amount=Balance.from_tao(amount=abs(amount)),
                hotkey_ss58=hotkey
            ))
            logger.info(success)
        except Exception as e:
            logger.error(f"Error unstaking amount: {amount}: {str(e)}", exc_info=True)
            success = False
    else:
        logger.info(f'Sentiment score is 0 so abandoning stake/unstake operation')
        return
        
    sentiment_data: Dict[str, Any] = {
        'netuid': netuid,
        'hotkey': hotkey,
        'sentiment_score': sentiment_score,
        'amount': amount,
        'operation': operation,
        'status': 'completed' if success else 'failed'
    }

    async def stake_store_async():
        """
        Store the stake operation details in the database.
        
        This function creates an async database session and stores the operation
        details in a single transaction. If any error occurs, the transaction
        is rolled back.
        """
        # Create a database session
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as db:
            try:
                # Add all objects to the session
                db.add(SentimentStakeOperation(**sentiment_data))
                await db.commit()

                logger.info(f"Successfully stored {sentiment_data}")
            except Exception as e:
                await db.rollback()
                logger.error(f"Error storing sentiment data: {str(e)}, data: {sentiment_data}", exc_info=True)

    # Use the helper function to run the async database operation
    run_async(stake_store_async())
