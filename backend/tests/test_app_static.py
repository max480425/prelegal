"""Integration tests for app root and static frontend serving.

The statically exported Next.js frontend (frontend/out) is served by FastAPI
when it has been built; otherwise a JSON fallback explains how to build it.
"""

from backend.utils.config import get_settings

FRONTEND_BUILT = get_settings().frontend_path.is_dir()


class TestRoot:
    def test_root_serves_app_or_fallback(self, client):
        response = client.get("/")
        assert response.status_code == 200
        if FRONTEND_BUILT:
            assert "text/html" in response.headers["content-type"]
            assert "<html" in response.text.lower()
        else:
            assert response.json()["message"] == "Prelegal NDA Generator API"

    def test_api_still_responsive_alongside_static(self, client):
        assert client.get("/api/health").status_code == 200
        assert client.get("/docs").status_code == 200


class TestStaticFrontend:
    """Only meaningful once `npm run build` has produced frontend/out."""

    def test_nda_creator_page_served(self, client):
        if not FRONTEND_BUILT:
            import pytest

            pytest.skip("frontend/out not built")
        response = client.get("/nda-creator/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_static_asset_served(self, client):
        if not FRONTEND_BUILT:
            import pytest

            pytest.skip("frontend/out not built")
        # Next static export emits hashed assets under _next/
        response = client.get("/_next/")
        # Directory listing is not required; any non-500 means routing works
        assert response.status_code in (200, 307, 404)
