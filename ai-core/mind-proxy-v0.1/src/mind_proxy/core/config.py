
from functools import lru_cache
from pydantic import BaseModel
import os

class Settings(BaseModel):
    host: str = os.getenv("MP_HOST", "127.0.0.1")
    port: int = int(os.getenv("MP_PORT", "7780"))
    log_level: str = os.getenv("MP_LOG_LEVEL", "info")
    allowed_origins: str = os.getenv("MP_ALLOWED_ORIGINS", "*")
    upstream_base_url: str = os.getenv("UPSTREAM_BASE_URL", "http://127.0.0.1:7790")
    upstream_timeout_seconds: float = float(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "30"))
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_tokens: int = int(os.getenv("RATE_LIMIT_TOKENS", "60"))
    rate_limit_refill_per_sec: float = float(os.getenv("RATE_LIMIT_REFILL_PER_SEC", "1"))
    cb_enabled: bool = os.getenv("CB_ENABLED", "true").lower() == "true"
    cb_fail_threshold: int = int(os.getenv("CB_FAIL_THRESHOLD", "5"))
    cb_cooldown_seconds: float = float(os.getenv("CB_COOLDOWN_SECONDS", "15"))
    redis_enabled: bool = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    redis_url: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

@lru_cache
def get_settings() -> Settings:
    return Settings()
