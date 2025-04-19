from functools import lru_cache
from typing import Any

from app.services.bittensor_service import BitTensorService
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str
    datura_api_key: str
    chutes_api_key: str
    redis_url: str = "redis://localhost:6379/0"
    database_url: str
    subtensor_network: str
    wallet_hotkey: str
    wallet_netuid: int
    wallet_name: str
    CACHE_EXPIRATION: int = 120  # Cache expiration time in seconds (2 minutes)

    model_config: SettingsConfigDict = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()

bts: BitTensorService = BitTensorService(
    netuid=settings.wallet_netuid,
    wallet_hotkey=settings.wallet_hotkey,
    wallet_name=settings.wallet_name
)
