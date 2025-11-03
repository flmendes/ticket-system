"""Centralized configuration management."""
from enum import Enum
from functools import lru_cache
from pydantic_settings import BaseSettings


class DeploymentMode(str, Enum):
    """Deployment mode selection."""
    MONOLITH = "monolith"
    MICROSERVICES = "microservices"


class Settings(BaseSettings):
    """Application settings."""

    # Deployment configuration
    deployment_mode: DeploymentMode = DeploymentMode.MICROSERVICES

    # Service info
    service_name: str = "ticket-system"
    environment: str = "development"

    # Server config
    host: str = "0.0.0.0"
    ticket_port: int = 8002
    vacancy_port: int = 8001
    monolith_port: int = 8000
    reload: bool = True

    # External services
    vacancy_url: str = "http://localhost:8001"
    vacancy_timeout: float = 2.0

    # Performance
    http_max_connections: int = 100
    http_keepalive_connections: int = 20

    # Stock config
    initial_stock: int = 1000
    cache_ttl_seconds: int = 1

    # Logging
    log_level: str = "INFO"
    json_logs: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
