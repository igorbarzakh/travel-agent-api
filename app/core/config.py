from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",)
    groq_api_key: str = Field(validation_alias="GROQ_API_KEY")
    groq_model: str = Field(validation_alias="GROQ_MODEL", default="openai/gpt-oss-20b")
    groq_url: str = Field(validation_alias="GROQ_URL", default="https://api.groq.com/openai/v1")


settings = Settings()