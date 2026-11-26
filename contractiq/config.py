from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    contractiq_database_url: str = "sqlite:///./contractiq.db"
    contractiq_max_upload_mb: int = 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
