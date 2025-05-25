import json

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TOKEN: str
    DB_URL: str
    API_KEY: str
    TON_WALLET_ADDRESS: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
