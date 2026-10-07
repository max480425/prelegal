"""Integration tests for the existing document API (regression coverage)."""

NDA_FIELDS = {
    "Purpose": "Evaluation of potential partnership and collaboration opportunities",
    "Effective Date": "2024-01-15",
    "MNDA Term": "2 years",
    "Term of Confidentiality": "3 years from the date of disclosure",
    "Governing Law": "California",
    "Jurisdiction": "Northern District of California",
}


class TestHealthAndInfo:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_info(self, client):
        response = client.get("/api/info")
        assert response.status_code == 200
        assert response.json()["name"] == "Prelegal NDA Generator API"


class TestTemplates:
    def test_list_templates(self, client):
        response = client.get("/api/templates")
        assert response.status_code == 200
        names = [t["name"] for t in response.json()]
        assert "Mutual-NDA" in names

    def test_template_schema(self, client):
        response = client.get("/api/templates/Mutual-NDA/schema")
        assert response.status_code == 200
        schema = response.json()
        assert schema["name"] == "Mutual-NDA"
        assert "Purpose" in schema["fields"]

    def test_unknown_template_404(self, client):
        assert client.get("/api/templates/Nope/schema").status_code == 404


class TestGenerateAndDownload:
    def test_generate_and_download(self, client):
        response = client.post(
            "/api/documents/generate",
            json={"template_name": "Mutual-NDA", "fields": NDA_FIELDS},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["document_id"]
        assert body["download_url"].endswith(body["document_id"])

        download = client.get(body["download_url"])
        assert download.status_code == 200
        assert download.headers["content-type"] == "application/pdf"
        assert download.content[:5] == b"%PDF-"

    def test_generate_missing_fields_400(self, client):
        response = client.post(
            "/api/documents/generate",
            json={"template_name": "Mutual-NDA", "fields": {"Purpose": "only one"}},
        )
        assert response.status_code == 400

    def test_generate_unknown_template_404(self, client):
        response = client.post(
            "/api/documents/generate",
            json={"template_name": "Not-A-Template", "fields": NDA_FIELDS},
        )
        assert response.status_code == 404
