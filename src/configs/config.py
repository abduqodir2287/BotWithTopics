from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = None
    # POSTGRES_DB: str = None
    # POSTGRES_HOST: str = None
    # POSTGRES_PORT: int = None
    # POSTGRES_USER: str = None
    # POSTGRES_PASSWORD: str = None
    #
    #
    #
    # @property
    # def DATABASE_URL(self) -> str:
    #     return (
    #         f"postgresql+asyncpg://{self.POSTGRES_USER}:"
    #         f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    #     )


    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()