from __future__ import annotations
import os
from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")
    environment: str = Field(default="development")
    azure_web_jobs_storage: Optional[str] = Field(default=None, alias="AzureWebJobsStorage")
    coinglass_api_key: Optional[str] = Field(default=None)
    coinglass_base_url: str = Field(default="https://open-api-v3.coinglass.com")
    binance_rest_base_url: str = Field(default="https://api.binance.com")
    binance_ws_base_url: str = Field(default="wss://stream.binance.com:9443")
    bybit_rest_base_url: str = Field(default="https://api.bybit.com")
    bybit_ws_base_url: str = Field(default="wss://stream.bybit.com/v5/public/linear")
    okx_rest_base_url: str = Field(default="https://www.okx.com")
    okx_ws_base_url: str = Field(default="wss://ws.okx.com:8443/ws/v5/public")
    key_vault_url: Optional[str] = Field(default=None)
    azure_storage_connection_string: Optional[str] = Field(default=None)
    chart_container_name: str = Field(default="charts")
    app_insights_connection_string: Optional[str] = Field(default=None)
    http_timeout_seconds: float = Field(default=15.0)
    http_max_retries: int = Field(default=4)
    http_retry_backoff_base: float = Field(default=0.8)
    candle_cache_ttl_seconds: int = Field(default=15)
    orderbook_cache_ttl_seconds: int = Field(default=5)
    funding_cache_ttl_seconds: int = Field(default=60)
    oi_cache_ttl_seconds: int = Field(default=30)
    lsr_cache_ttl_seconds: int = Field(default=300)
    liquidation_cache_ttl_seconds: int = Field(default=300)
    chart_sas_ttl_minutes: int = Field(default=60)

    @field_validator("environment")
    @classmethod
    def _normalize_environment(cls, v: str) -> str:
        v = (v or "development").strip().lower()
        allowed = {"development", "staging", "production"}
        if v not in allowed: raise ValueError(f"environment must be one of {allowed}, got {v!r}")
        return v

    @property
    def is_production(self) -> bool: return self.environment == "production"
    @property
    def is_development(self) -> bool: return self.environment == "development"

    def require_secret(self, name: str) -> str:
        value = getattr(self, name, None)
        if not value: raise RuntimeError(f"Required secret '{name}' is not configured.")
        return value

@lru_cache(maxsize=1)
def get_settings() -> Settings: return Settings()

def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()

settings: Settings = get_settings()