import os
from pydantic import BaseModel, Field, ValidationError

class LLMConfig(BaseModel):
    base_url: str = Field(default=os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434"))
    model: str = Field(default=os.getenv("LLM_MODEL", "llama3.1:8b-instruct-q4_K_M"))
    timeout: float = Field(default=float(os.getenv("LLM_TIMEOUT", "60")))
    max_tokens: int = Field(default=int(os.getenv("LLM_MAX_TOKENS", "1024")))
    keep_alive: str = Field(default=os.getenv("LLM_KEEP_ALIVE", "5m"))

def get_llm_config() -> LLMConfig:
    try:
        return LLMConfig()
    except ValidationError:
        return LLMConfig()
