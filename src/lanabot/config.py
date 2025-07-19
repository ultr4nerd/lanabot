"""Configuration settings for LanaBot."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")

    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")

    # WhatsApp Business Cloud API Configuration (Meta)
    meta_access_token: str = Field(..., description="Meta Access Token")
    meta_phone_number_id: str = Field(..., description="Meta Phone Number ID")
    meta_business_account_id: str = Field(..., description="Meta Business Account ID")
    meta_app_id: str = Field(..., description="Meta App ID")
    meta_app_secret: str = Field(..., description="Meta App Secret")
    meta_webhook_verify_token: str = Field(..., description="Meta Webhook Verify Token")
    meta_whatsapp_number: str = Field(..., description="Meta WhatsApp number")

    # Application Configuration
    port: int = Field(default=8000, description="Application port")
    host: str = Field(default="0.0.0.0", description="Application host")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log level"
    )

    # Business Logic Configuration
    minimum_balance_alert: float = Field(
        default=500.0, description="Minimum balance to trigger alert"
    )
    default_currency: str = Field(default="MXN", description="Default currency")

    # Railway/Production Configuration
    railway_environment: str = Field(
        default="development", description="Railway environment"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
