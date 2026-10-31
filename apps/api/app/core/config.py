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
    jwt_secret_key: str = "dev-secret-key-change-in-production-only-32bytes-minimum"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24
    jwt_refresh_token_expire_minutes: int = 60 * 24 * 7
    openrouter_api_key: str = ""
    gemini_api_key: str = ""


settings = Settings()
