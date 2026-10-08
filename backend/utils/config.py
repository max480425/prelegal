from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
import secrets

# Repository root (prelegal/), anchored to this file so paths never depend
# on the process working directory.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _resolve(raw: str, base: Path, mkdir: bool = False) -> Path:
    """Resolve a possibly-relative path against the repo root."""
    path = Path(raw)
    if not path.is_absolute():
        path = base / path
    if mkdir:
        path.mkdir(parents=True, exist_ok=True)
    return path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    DOCUMENTS_DIR: str = "generated_documents"
    TEMPLATES_DIR: str = "templates"
    FRONTEND_DIR: str = "frontend/out"
    DATABASE_PATH: str = "prelegal.db"
    # Empty => a random secret is generated at startup (see model_post_init),
    # so a known default can never be used to forge session tokens.
    JWT_SECRET: str = ""
    JWT_EXPIRE_MINUTES: int = 1440
    LOG_LEVEL: str = "INFO"
    # Read from the repo-root .env; passed to litellm explicitly as api_key=
    # (pydantic-settings never exports .env keys to os.environ, so LiteLLM's
    # own env lookup would not find it).
    OPENROUTER_API_KEY: str = ""
    # Max chat requests per IP per minute (0 disables the limiter). Chat is
    # public and every turn spends OpenRouter credit.
    CHAT_RATE_LIMIT: int = 20

    class Config:
        # Anchor .env to the repo root (not CWD). Unrelated keys in the same
        # file are ignored via extra="ignore"; OPENROUTER_API_KEY is a field.
        env_file = str(BASE_DIR / ".env")
        case_sensitive = True
        extra = "ignore"

    def model_post_init(self, __context) -> None:
        if not self.JWT_SECRET:
            self.JWT_SECRET = secrets.token_hex(32)

    @property
    def allowed_origins_list(self) -> list:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def documents_path(self) -> Path:
        return _resolve(self.DOCUMENTS_DIR, BASE_DIR, mkdir=True)

    @property
    def templates_path(self) -> Path:
        return _resolve(self.TEMPLATES_DIR, BASE_DIR)

    @property
    def frontend_path(self) -> Path:
        """Path to the statically exported frontend (may not exist in dev)."""
        return _resolve(self.FRONTEND_DIR, BASE_DIR)

    @property
    def database_path(self) -> Path:
        return _resolve(self.DATABASE_PATH, BASE_DIR)


@lru_cache
def get_settings() -> Settings:
    return Settings()
