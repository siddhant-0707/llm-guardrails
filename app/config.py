"""Application configuration using Pydantic Settings"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=False)
    environment: Literal["development", "staging", "production"] = Field(default="development")

    # Redis Configuration
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: str | None = Field(default=None)

    # OpenTelemetry Configuration
    otel_service_name: str = Field(default="llm-guardrails")
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317")
    otel_log_level: str = Field(default="INFO")

    # LLM Provider Configuration
    google_api_key: str | None = Field(default=None, description="Google Gemini API key")
    google_model: str = Field(default="gemini-pro", description="Google Gemini model name")
    # Optional: Other providers
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo-preview")
    anthropic_api_key: str | None = Field(default=None)
    cohere_api_key: str | None = Field(default=None)

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=60)
    rate_limit_requests_per_hour: int = Field(default=1000)

    # Guardrails Configuration
    guardrails_enabled: bool = Field(default=True)
    pii_redaction_enabled: bool = Field(default=True)
    content_policy_enabled: bool = Field(default=True)
    prompt_injection_detection_enabled: bool = Field(default=True)

    # Vector Database Configuration
    vector_db_type: Literal["faiss", "pgvector", "qdrant"] = Field(default="faiss")
    pgvector_host: str = Field(default="localhost")
    pgvector_port: int = Field(default=5432)
    pgvector_db: str = Field(default="vectorstore")
    pgvector_user: str = Field(default="postgres")
    pgvector_password: str = Field(default="postgres")
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)

    # MLflow Configuration
    mlflow_tracking_uri: str = Field(default="http://localhost:5000")
    mlflow_experiment_name: str = Field(default="llm-guardrails-experiments")

    # Mem0 Configuration
    mem0_api_key: str | None = Field(default=None)

    # Security
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def pgvector_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return (
            f"postgresql://{self.pgvector_user}:{self.pgvector_password}"
            f"@{self.pgvector_host}:{self.pgvector_port}/{self.pgvector_db}"
        )

    @property
    def qdrant_url(self) -> str:
        """Construct Qdrant URL"""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

