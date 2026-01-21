from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "Auto PM"
    debug: bool = False

    # Database (SQLite for local dev, PostgreSQL for production)
    database_url: str = "sqlite:///./autopm.db"

    # LLM Configuration
    llm_provider: str = "stub"  # "stub" or "azure_openai"

    # Azure OpenAI
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: str = "gpt-4"
    azure_openai_api_version: str = "2024-02-15-preview"

    # Sprint defaults
    default_sprint_length_days: int = 14

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
