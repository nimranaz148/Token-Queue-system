from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clinic_dev"
    port: int = 8000
    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    supabase_service_role_key: str = ""
    jwt_secret_key: str = "dev-secret-key-change-in-production-only-32bytes-minimum"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24
    jwt_refresh_token_expire_minutes: int = 60 * 24 * 7
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "openai/gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_default_model: str = "gemini-1.5-flash"
    ai_clinic_monthly_cap_usd: float = 2.0
    ai_global_monthly_cap_usd: float = 50.0


settings = Settings()
