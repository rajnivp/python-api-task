from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.bittensor_service import BitTensorService


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
    postgres_user: str
    postgres_password: str
    postgres_db: str
    CACHE_EXPIRATION: int = 120  # REDIS Cache expiration time in seconds (2 minutes)

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
