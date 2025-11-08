"""Application settings using Pydantic BaseSettings.

NO business logic, NO functions - pure configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings - pure configuration only."""

    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/image_frames"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Image Processing
    compression_level: int = 9
    image_resized_width: int = 150
    image_original_width: int = 200

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Monitoring
    prometheus_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()

