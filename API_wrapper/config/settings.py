"""
Configuration settings for Animal Encyclopedia AI Wrapper
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # API Configuration
    APP_NAME: str = "Animal Encyclopedia AI"
    APP_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""  # Optional: only needed for LLM responses
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # FREE local model
    LLM_MODEL: str = "gpt-4o-mini"  # Cost-effective model for testing
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 800

    # Semantic Routing Thresholds
    ACCEPT_THRESHOLD: float = 0.72
    REJECT_THRESHOLD: float = 0.45
    NEGATIVE_CHECK_THRESHOLD: float = 0.60

    # Semantic Cache Configuration
    CACHE_HIT_THRESHOLD: float = 0.95
    MAX_CACHE_SIZE: int = 10000
    CACHE_TTL_HOURS: int = 168  # 7 days

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Context Management
    MAX_CONTEXT_TOKENS: int = 1500
    MAX_HISTORY_TURNS: int = 5

    # Anaphora Resolution
    CONTEXT_WINDOW: int = 3

    # Context Caching
    CONTEXT_CACHE_THRESHOLD: int = 3

    # File Paths
    DATA_DIR: str = "data"
    VECTOR_DB_PATH: str = "data/vector_store"
    ANCHOR_DATASET_PATH: str = "data/anchor_dataset.json"

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
