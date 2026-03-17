from pathlib import Path
import sys

from fastapi.testclient import TestClient

# Ensure the agent-backend root (where main.py lives) is on sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import app, _run_agent


client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_chat_uses_run_agent(monkeypatch):
    calls = {}

    def fake_run_agent(message: str, history=None) -> str:
        calls["message"] = message
        calls["history"] = history or []
        return f"echo: {message}"

    monkeypatch.setattr("main._run_agent", fake_run_agent)

    payload = {
        "message": "Find First Amendment cases",
        "history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi, how can I help?"},
        ],
    }
    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == "echo: Find First Amendment cases"

    assert calls["message"] == "Find First Amendment cases"
    # ChatRequest converts history entries to Pydantic models; we pass model_dump() into _run_agent
    assert len(calls["history"]) == 2
    assert calls["history"][0]["role"] == "user"
    assert calls["history"][0]["content"] == "Hello"
    assert calls["history"][1]["role"] == "assistant"
    assert calls["history"][1]["content"] == "Hi, how can I help?"


def test_run_agent_requires_api_key(monkeypatch):
    # Simulate missing OPENAI_API_KEY
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        _run_agent("test")
    except ValueError as e:
        assert "OPENAI_API_KEY is not set" in str(e)
    else:
        raise AssertionError("Expected ValueError when OPENAI_API_KEY is missing")

