import httpx
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_search_case_law_normalized(monkeypatch):
    """Smoke test: /search/case-law returns normalized structure when CourtListener responds."""

    class DummyResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "count": 1,
                "results": [
                    {
                        "caseName": "Example v. Test",
                        "court": "U.S. Supreme Court",
                        "dateFiled": "2000-01-01",
                        "snippet": "Example snippet",
                        "citation": ["123 U.S. 456"],
                        "absolute_url": "/opinion/123/example-v-test/",
                        "opinions": [],
                    }
                ],
            }

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            return DummyResponse()

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    resp = client.get("/search/case-law", params={"q": "example", "page_size": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["case_name"] == "Example v. Test"
    assert result["court"] == "U.S. Supreme Court"
    assert result["date_filed"] == "2000-01-01"
    assert result["snippet"]
    assert result["citations"] == ["123 U.S. 456"]
    assert result["url"].endswith("/opinion/123/example-v-test/")


def test_search_dockets_normalized(monkeypatch):
    """Smoke test: /search/dockets returns normalized structure when CourtListener responds."""

    class DummyResponse:
        def __init__(self) -> None:
            self.status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "count": 1,
                "results": [
                    {
                        "caseName": "Example v. Test",
                        "court": "D. Minn.",
                        "docketNumber": "0:23-cv-00001",
                        "snippet": "Docket snippet",
                        "absolute_url": "/docket/0:23-cv-00001-example-v-test/",
                    }
                ],
            }

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            return DummyResponse()

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    resp = client.get("/search/dockets", params={"q": "example docket", "page_size": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["case_name"] == "Example v. Test"
    assert result["court"] == "D. Minn."
    assert result["docket_number"] == "0:23-cv-00001"
    assert result["snippet"]
    assert result["url"].endswith("/docket/0:23-cv-00001-example-v-test/")

