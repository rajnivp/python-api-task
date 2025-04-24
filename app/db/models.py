"""
Database models for the TAO Dividend Sentiment Service.

This module defines SQLAlchemy models for storing dividend data and sentiment-based
staking operations. It includes models for tracking dividends received by validators
and the sentiment analysis and staking operations performed on those dividends.
"""

import asyncio
from datetime import datetime
from typing import Optional, ClassVar

from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.database import Base, engine


class Dividend(Base):
    """
    Model for storing dividend data received by validators.
    
    Attributes:
        id (int): Primary key
        netuid (int): Network UID of the validator
        hotkey (str): Hotkey of the validator
        amount (float): Dividend amount received
        timestamp (datetime): When the dividend was received
    """
    __tablename__: ClassVar[str] = "dividends"

    id: int = Column(Integer, primary_key=True, index=True)
    netuid: int = Column(Integer, nullable=False)
    hotkey: str = Column(String, nullable=False)
    amount: float = Column(Float, nullable=False)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)


class SentimentStakeOperation(Base):
    """
    Model for tracking sentiment analysis and staking operations.
    
    Attributes:
        id (int): Primary key
        netuid (int): Network UID of the validator
        hotkey (str): Hotkey of the validator
        sentiment_score (float): Sentiment analysis score (optional)
        amount (float): Amount staked/unstaked (positive for stake, negative for unstake)
        transaction_hash (str): Blockchain transaction hash (optional)
        operation (str): Type of operation performed
        status (str): Operation status ('completed' or 'failed')
        created_at (datetime): When the operation was created
        completed_at (datetime): When the operation was completed (optional)
    """
    __tablename__: ClassVar[str] = "sentiment_stake_operations"

    id: int = Column(Integer, primary_key=True, index=True)
    netuid: int = Column(Integer, nullable=False)
    hotkey: str = Column(String, nullable=False)
    sentiment_score: Optional[float] = Column(Float, nullable=True)
    amount: float = Column(Float, nullable=False)  # Positive for stake, negative for unstake
    transaction_hash: Optional[str] = Column(String, nullable=True)  # Blockchain transaction hash
    operation: str = Column(String, nullable=False)
    status: str = Column(String, nullable=False)  # 'completed', 'failed'
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)


async def init_models() -> None:
    """
    Initialize database models by creating all tables.
    This function is called when the application starts.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def run_async(func):
    """
    Decorator to safely run async functions in both sync and async contexts.
    
    Args:
        func: Async function to be executed
        
    Returns:
        Future or result of the async function
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an existing event loop (e.g., FastAPI)
        return asyncio.ensure_future(func())
    else:
        # No loop running - safe to use asyncio.run()
        return asyncio.run(func())


# Call it safely
run_async(init_models)
