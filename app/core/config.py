"""
Configuration settings for the TAO Dividend Sentiment Service.

This module defines the application settings using Pydantic's BaseSettings,
which automatically loads configuration from environment variables and .env file.
It also initializes the BitTensorService with the configured settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.bittensor_service import BitTensorService


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        api_key (str): API key for authentication
        datura_api_key (str): API key for Datura service
        chutes_api_key (str): API key for Chutes service
        redis_url (str): Redis connection URL
        redis_port (int): Redis port number
        database_url (str): PostgreSQL database connection URL
        subtensor_network (str): Bittensor network name
        wallet_hotkey (str): Bittensor wallet hotkey
        wallet_netuid (int): Bittensor network UID
        wallet_name (str): Bittensor wallet name
        postgres_user (str): PostgreSQL database user
        postgres_password (str): PostgreSQL database password
        postgres_db (str): PostgreSQL database name
        CACHE_EXPIRATION (int): Redis cache expiration time in seconds (default: 120)
    """
    api_key: str
    datura_api_key: str
    chutes_api_key: str
    redis_url: str
    redis_port: int
    database_url: str
    subtensor_network: str
    wallet_hotkey: str
    wallet_netuid: int
    wallet_name: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    CACHE_EXPIRATION: int = 120  # REDIS Cache expiration time in seconds (2 minutes)

    model_config: SettingsConfigDict = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


settings: Settings = get_settings()

bts: BitTensorService = BitTensorService(
    netuid=settings.wallet_netuid,
    wallet_hotkey=settings.wallet_hotkey,
    wallet_name=settings.wallet_name
)
