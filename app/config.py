from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str

    # Telegram
    BOT_TOKEN: str
    ALLOWED_USER_IDS: list[int]

    # App
    BASE_URL: str = "http://localhost:8000"
    STATIC_DIR: str = "app/static"


settings = Settings()
