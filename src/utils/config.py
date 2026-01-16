from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
from pathlib import Path

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    PROJECT_NAME: str = "EU AI GDPR Navigator"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Vector DB
    CHROMA_PERSIST_DIRECTORY: Path = DATA_DIR / "chroma"

settings = Settings()
