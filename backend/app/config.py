"""
Configuration management module with environment variable support.
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database configuration
    database_url: str = "sqlite:///./data/app.db"
    
    # AI service configuration
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model_name: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-3-small"  # Embedding模型
    
    # ChromaDB configuration
    chroma_persist_directory: str = "./data/chroma"
    chroma_host: Optional[str] = None
    chroma_port: Optional[int] = None
    
    # Application settings
    app_name: str = "Diet Training Tracker"
    debug: bool = False
    
    # MySQL specific settings (if using MySQL)
    mysql_root_password: Optional[str] = None
    mysql_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
