from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Repository root (prelegal/), anchored to this file so paths never depend
# on the process working directory.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    DOCUMENTS_DIR: str = "generated_documents"
    TEMPLATES_DIR: str = "templates"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_origins_list(self) -> list:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def documents_path(self) -> Path:
        path = Path(self.DOCUMENTS_DIR)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def templates_path(self) -> Path:
        path = Path(self.TEMPLATES_DIR)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
