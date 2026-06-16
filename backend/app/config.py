"""Application configuration via pydantic-settings.

All runtime configuration is read from environment variables (or a local .env
file). Keeping it in one typed Settings object means every module reads the same
validated values and there are no scattered os.getenv calls.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "AI Research Copilot"
    environment: str = "development"
    log_level: str = "INFO"

    # LLM (OpenAI)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_fast_model: str = "gpt-4o-mini"

    # Web research (Tavily)
    tavily_api_key: str = ""
    tavily_max_results: int = 5

    # Database
    database_url: str = "postgresql+psycopg://copilot:copilot@localhost:5432/copilot"

    # Workflow tuning
    quality_threshold: float = 0.7
    max_research_retries: int = 2

    # API
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]

    @property
    def mock_mode(self) -> bool:
        """Run the graph without external LLM calls when no OpenAI key is set."""
        return not self.openai_api_key

    @property
    def use_real_search(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def checkpointer_dsn(self) -> str:
        """Plain psycopg DSN for the LangGraph Postgres checkpointer.

        SQLAlchemy needs the ``+psycopg`` driver suffix; psycopg itself does not.
        """
        return self.database_url.replace("+psycopg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
