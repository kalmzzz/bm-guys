from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development")
    port: int = Field(default=8080)

    # Database
    database_url: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")


settings = Settings()