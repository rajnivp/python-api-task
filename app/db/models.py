import asyncio
from datetime import datetime
from typing import Optional, ClassVar

from sqlalchemy import Column, Integer, String, Float, DateTime

from app.db.database import Base, engine


class Dividend(Base):
    __tablename__: ClassVar[str] = "dividends"

    id: int = Column(Integer, primary_key=True, index=True)
    netuid: int = Column(Integer, nullable=False)
    hotkey: str = Column(String, nullable=False)
    amount: float = Column(Float, nullable=False)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)


class SentimentStakeOperation(Base):
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(init_models())
