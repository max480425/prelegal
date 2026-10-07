"""Tests for settings resolution and the JWT secret default."""

from backend.utils.config import Settings


class TestJwtSecret:
    def test_random_secret_generated_when_unset(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        settings = Settings(JWT_SECRET="")
        # No hardcoded default: a long random secret is generated instead.
        assert settings.JWT_SECRET
        assert settings.JWT_SECRET != "dev-secret-change-me"
        assert len(settings.JWT_SECRET) >= 32

    def test_random_secret_differs_between_instances(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        first = Settings(JWT_SECRET="")
        second = Settings(JWT_SECRET="")
        assert first.JWT_SECRET != second.JWT_SECRET

    def test_explicit_secret_respected(self):
        settings = Settings(JWT_SECRET="an-explicit-secret-for-tests")
        assert settings.JWT_SECRET == "an-explicit-secret-for-tests"


class TestPathResolution:
    def test_relative_paths_anchor_to_repo_root(self):
        from backend.utils.config import BASE_DIR

        settings = Settings(DATABASE_PATH="x.db", TEMPLATES_DIR="templates")
        assert settings.database_path == BASE_DIR / "x.db"
        assert settings.templates_path == BASE_DIR / "templates"

    def test_relative_documents_dir_created_under_base(self, monkeypatch, tmp_path):
        import backend.utils.config as config

        monkeypatch.setattr(config, "BASE_DIR", tmp_path)
        settings = Settings(DOCUMENTS_DIR="docs")
        assert settings.documents_path == tmp_path / "docs"
        assert (tmp_path / "docs").is_dir()

    def test_absolute_paths_kept(self, tmp_path):
        settings = Settings(DATABASE_PATH=str(tmp_path / "abs.db"))
        assert settings.database_path == tmp_path / "abs.db"
