from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    TG_BOT_API_KEY: str
    PIXABAY_API_KEY: str
    PIXABAY_BASE_URL: str = "https://pixabay.com/api/"


config = Config()
