from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # -------------------------
    # Application
    # -------------------------

    APP_NAME: str = "RAG Q&A Application"
    DEBUG: bool = True

    # -------------------------
    # Database
    # -------------------------

    DATABASE_URL: str

    # -------------------------
    # AWS / S3
    # -------------------------

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_DEFAULT_REGION: str
    AWS_BUCKET: str

    # -------------------------
    # JWT
    # -------------------------

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()