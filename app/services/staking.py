import asyncio
from typing import Dict, Any, Optional

from bittensor_cli.cli import Balance

from app.core.config import bts
from app.core.logger import logger
from app.db.database import create_async_engine, sessionmaker, settings, AsyncSession
from app.db.models import SentimentStakeOperation


def submit_stake_adjustment(
        sentiment_score: Optional[float],
        netuid: int,
        hotkey: str
) -> None:
    amount = 0.1 * sentiment_score
    if sentiment_score > 0:
        operation = 'stake'
        try:
            loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(bts.add_stake(wallet=bts.wallet, netuid=netuid,
                                                            amount=Balance.from_tao(amount=amount), hotkey_ss58=hotkey))
            logger.info(success)
            loop.close()
        except Exception as e:
            logger.error(f"Error staking amount: {amount}: {str(e)}", exc_info=True)
            success = False

    elif sentiment_score < 0:
        operation = 'unstake'
        try:
            loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(bts.unstake(wallet=bts.wallet, netuid=netuid,
                                                          amount=Balance.from_tao(amount=abs(amount)),
                                                          hotkey_ss58=hotkey))
            logger.info(success)
            loop.close()
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

    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stake_store_async())
    loop.close()
