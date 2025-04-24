"""
Database configuration for the TAO Dividend Sentiment Service.

This module sets up the SQLAlchemy async database connection and session management,
including the async engine and session factory configuration.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Create the async engine
engine = create_async_engine(settings.database_url, echo=False, future=True)

# Create the async session instance directly
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

