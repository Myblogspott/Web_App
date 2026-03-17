# Agentic Web App with API Wrapper

A full-stack agent-driven app: **Frontend** → **LLM Agent Backend** (LangChain, tool calling) → **MCP Server** (API wrapper) → **CourtListener** (legal search).

## Architecture

- **Frontend** (React + Vite): User types a natural-language question; receives the agent’s answer.
- **Agent Backend** (Python, FastAPI, LangChain): Interprets intent, calls MCP tools, returns a concise answer.
- **MCP Server** (Python, FastAPI, LangChain): Wraps the CourtListener Legal Search API using LangChain runnables; exposes normalized `/search/case-law` and `/search/dockets`.

**LangChain usage:** The **agent-backend** uses LangChain’s `ChatOpenAI`, `bind_tools`, and `SystemMessage`/`HumanMessage`/`ToolMessage` for the LLM tool-calling loop (model: **gpt-5-mini-2025-08-07**; no GPT-4). The **mcp-server** uses LangChain’s `RunnableLambda` to fetch and normalize CourtListener API responses. See [agent-backend/README.md](agent-backend/README.md) and [mcp-server/README.md](mcp-server/README.md) for details.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the diagram and separation of concerns. API choice and endpoints are documented in [docs/API_DISCOVERY.md](docs/API_DISCOVERY.md).

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend)
- An OpenAI API key (for the agent backend)
- A CourtListener API token (for the MCP Server; [get one here](https://www.courtlistener.com/help/api/rest/#your-authorization-token))

### 1. Clone and environment

```bash
git clone <repo-url>
cd <repo>
cp .env.example .env
# Edit .env: set OPENAI_API_KEY and COURTLISTENER_API_TOKEN
```

### 2. Python (MCP Server + Agent Backend)

Use a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Environment variables

| Variable | Where | Required | Description |
|----------|--------|----------|-------------|
| `OPENAI_API_KEY` | Agent backend | Yes | OpenAI API key for the LLM. |
| `COURTLISTENER_API_TOKEN` | MCP Server | Yes | CourtListener API token for legal search. |
| `MCP_SERVER_URL` | Agent backend | No | Default `http://localhost:8001`. Base URL of the MCP Server. |

Never commit `.env`. Use `.env.example` as a template.

---

## Run (three terminals)

1. **MCP Server** (port 8001)

   ```bash
   source .venv/bin/activate
   cd mcp-server
   uvicorn main:app --reload --port 8001
   ```

2. **Agent Backend** (port 8000)

   ```bash
   source .venv/bin/activate
   cd agent-backend
   uvicorn main:app --reload --port 8000
   ```

3. **Frontend** (port 5173)

   ```bash
   cd frontend
   npm run dev
   ```

Open http://localhost:5173 and try e.g. “Find cases on first amendment free speech” or “Search dockets for civil rights.”

---

## Dependencies

- **Python:** [requirements.txt](requirements.txt) — FastAPI, uvicorn, httpx, pydantic, python-dotenv, LangChain, langchain-openai, pytest.
- **Frontend:** [frontend/package.json](frontend/package.json) — React 18, Vite 5.

Versions are pinned where necessary for reproducibility.

---

## Security

- **API keys:** Stored only in `.env` (or environment). Not committed. The agent backend reads `OPENAI_API_KEY`; the MCP Server reads `COURTLISTENER_API_TOKEN` and never exposes it to the frontend.
- **Network:** The frontend talks only to the Agent Backend (same origin or proxy). The Agent Backend calls the MCP Server; the MCP Server calls CourtListener. No third-party keys are exposed to the browser.

---

## Deployment (overview)

For production you would typically:

- **Containers:** Run MCP Server, Agent Backend, and a static frontend (e.g. nginx serving `frontend/dist`) in separate containers; use Docker Compose or Kubernetes for orchestration.
- **Serverless:** Agent Backend and MCP Server could be deployed as serverless functions (e.g. AWS Lambda, Google Cloud Functions) behind an API gateway; frontend as static hosting (S3 + CloudFront, Vercel, etc.).
- **Secrets:** Use the platform’s secret manager for `OPENAI_API_KEY` and `COURTLISTENER_API_TOKEN`; keep `MCP_SERVER_URL` configurable per environment.

---

## Documentation for new developers

- **README.md** (this file): Setup, run, env vars, high-level architecture.
- **ARCHITECTURE.md:** Data flow, separation of concerns, security.
- **docs/API_DISCOVERY.md:** Chosen API (CourtListener), endpoints, and how the MCP uses them.
- **mcp-server/README.md** and **agent-backend/README.md:** How to run each service and what they expose.

Assumptions for someone taking over or collaborating:

- All secrets live in environment (or `.env` locally); never in code.
- The repo is self-contained: clone, set `OPENAI_API_KEY` and `COURTLISTENER_API_TOKEN`, run the three components as above.
- Tests:
  - MCP Server: `cd mcp-server && pytest -v`
  - Agent Backend: `cd agent-backend && pytest -v`
