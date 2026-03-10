from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = 'postgresql+psycopg2://linkedin:linkedin@postgres:5432/linkedin_lead'
    celery_broker_url: str = 'redis://redis:6379/1'
    celery_result_backend: str = 'redis://redis:6379/2'
    playwright_headless: bool = True
    playwright_timeout_ms: int = 30000
    linkedin_cookies_json: str | None = None
    linkedin_storage_state_path: str | None = None

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
