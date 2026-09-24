from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    groq_api_key: str = Field(validation_alias="GROQ_API_KEY")
    groq_model: str = Field(validation_alias="GROQ_MODEL", default="openai/gpt-oss-20b")
    groq_url: str = Field(
        validation_alias="GROQ_URL", default="https://api.groq.com/openai/v1"
    )

    database_url: str = Field(
        validation_alias="DATABASE_URL",
    )

    jwt_secret: str = Field(
        validation_alias="JWT_SECRET",
    )

    jwt_algorithm: str = Field(
        validation_alias="JWT_ALGORITHM",
        default="HS256",
    )

    access_token_expire_minutes: int = Field(
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        default=15,
    )

    refresh_token_expire_days: int = Field(
        validation_alias="REFRESH_TOKEN_EXPIRE_DAYS",
        default=30,
    )

    refresh_cookie_name: str = Field(
        validation_alias="REFRESH_COOKIE_NAME",
        default="refresh_token",
    )

    cookie_secure: bool = Field(
        validation_alias="COOKIE_SECURE",
        default=False,
    )

    cookie_same_site: str = Field(
        validation_alias="COOKIE_SAMESITE",
        default="lax",
    )


settings = Settings()
