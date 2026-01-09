from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()