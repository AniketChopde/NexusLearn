"""
Configuration module for the AI Study Planner backend.
Loads and validates all environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Settings
    app_name: str = "AI Study Planner"
    app_version: str = "1.0.0"
    debug: bool = False
    allowed_origins: str = "http://localhost:3000,http://20.81.196.215:5173"
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")
    
    # Azure OpenAI Configuration (Chat/LLM)
    azure_openai_endpoint: str = Field(..., alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(..., alias="AZURE_OPENAI_API_KEY")
    azure_openai_deployment: str = Field(default="gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2024-05-01-preview", alias="AZURE_OPENAI_API_VERSION")
    
    # Azure OpenAI Embedding Configuration (can be different resource)
    azure_openai_embedding_endpoint: str = Field(..., alias="AZURE_OPENAI_EMBEDDING_ENDPOINT")
    azure_openai_embedding_key: str = Field(..., alias="AZURE_OPENAI_EMBEDDING_API_KEY")
    azure_openai_embedding_deployment: str = Field(default="text-embedding-3-small", alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    
    # Database Configuration
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 86400  # 24 hours
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Vector Store Configuration
    chroma_persist_directory: str = "./chroma_db"
    vector_store_api_key: str = ""
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    serpapi_api_key: str = ""
    duckduckgo_rate_limit: int = 10
    duckduckgo_enable_fallback: bool = True
    force_mock_mode: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Email Configuration
    mail_username: str = Field(default="", alias="SMTP_USER")
    mail_password: str = Field(default="", alias="SMTP_PASSWORD")
    mail_from: str = Field(default="", alias="SMTP_FROM")
    mail_port: int = Field(default=587, alias="SMTP_PORT")
    mail_server: str = Field(default="", alias="SMTP_HOST")
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    use_credentials: bool = True
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def jwt_access_token_expire_seconds(self) -> int:
        """Convert access token expiry to seconds."""
        return self.jwt_access_token_expire_minutes * 60
    
    @property
    def jwt_refresh_token_expire_seconds(self) -> int:
        """Convert refresh token expiry to seconds."""
        return self.jwt_refresh_token_expire_days * 24 * 60 * 60


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This ensures settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
