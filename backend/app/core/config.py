"""
Application configuration management using Pydantic and environment variables.
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_debug: bool = Field(default=False, env="API_DEBUG")

    # LiveKit Configuration
    livekit_api_key: str = Field(..., env="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(..., env="LIVEKIT_API_SECRET")
    livekit_ws_url: str = Field(..., env="LIVEKIT_WS_URL")
    livekit_worker_port: int = Field(default=8080, env="LIVEKIT_WORKER_PORT")

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")

    # ElevenLabs Configuration
    elevenlabs_api_key: str = Field(..., env="ELEVENLABS_API_KEY")

    # Deepgram Configuration
    deepgram_api_key: str = Field(..., env="DEEPGRAM_API_KEY")

    # Supabase Configuration
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")

    # Application Settings
    app_name: str = "Translation Service API"
    app_version: str = "1.0.0"
    app_description: str = "Real-time translation service using LiveKit and AI"

    # CORS Settings
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
