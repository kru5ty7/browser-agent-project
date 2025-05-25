"""Configuration settings for the browser agent."""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")

    # Browser Configuration
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")  # milliseconds
    browser_viewport_width: int = Field(default=1920, env="BROWSER_WIDTH")
    browser_viewport_height: int = Field(default=1080, env="BROWSER_HEIGHT")

    # Agent Configuration
    agent_max_steps: int = Field(default=10, env="AGENT_MAX_STEPS")
    agent_retry_attempts: int = Field(default=3, env="AGENT_RETRY_ATTEMPTS")
    agent_retry_delay: float = Field(default=1.0, env="AGENT_RETRY_DELAY")

    # LLM Configuration
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.0, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        env="LOG_FORMAT"
    )
    log_file: Optional[str] = Field(default="logs/agent.log", env="LOG_FILE")

    # Performance
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # seconds

    # Security
    allowed_domains: List[str] = Field(default_factory=list, env="ALLOWED_DOMAINS")
    rate_limit_calls: int = Field(default=100, env="RATE_LIMIT_CALLS")
    rate_limit_period: int = Field(default=3600, env="RATE_LIMIT_PERIOD")  # seconds

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def parse_allowed_domains(cls, v):
        if isinstance(v, str):
            return [d.strip() for d in v.split(",") if d.strip()]
        return v or []

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        if v:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if v.upper() not in valid_levels:
                raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
            return v.upper()
        return "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Handle missing .env file gracefully
        env_file_load = True


# Create settings instance with error handling
try:
    settings = Settings()
except Exception as e:
    print(f"Warning: Error loading settings: {e}")
    print("Using default settings. Make sure .env file exists and is properly formatted.")
    # Create settings with defaults
    settings = Settings(_env_file=None)
