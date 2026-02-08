"""Application configuration."""
from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    app_name: str = "Networking Automation Engine"
    app_version: str = "1.0.0"
    app_description: str = "AI-assisted networking automation tool for L2/L3 topology and configuration generation"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Template Configuration
    template_directory: str = "./templates"
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # CORS Configuration
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    class Config:
        """Pydantic config."""
        case_sensitive = False
        env_file = ".env"


# Create global settings instance
settings = Settings()
