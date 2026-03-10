from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = 'development'
    log_level: str = 'INFO'
    secret_key: str = 'change_me'
    access_token_expire_minutes: int = 60

    database_url: str = 'postgresql+psycopg2://linkedin:linkedin@postgres:5432/linkedin_lead'
    redis_url: str = 'redis://redis:6379/0'
    celery_broker_url: str = 'redis://redis:6379/1'
    celery_result_backend: str = 'redis://redis:6379/2'

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
