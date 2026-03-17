# MCP Server (CourtListener API Wrapper)

LangChain-wrapped CourtListener Legal Search API. Uses **LangChain runnables** (`RunnableLambda`) to fetch from CourtListener and normalize responses; FastAPI endpoints invoke these runnables. Exposes normalized search endpoints for the agent backend.

## LangChain usage

- **RunnableLambda** (`langchain_core.runnables`): Async runnables `_fetch_case_law_impl` and `_fetch_dockets_impl` perform the CourtListener HTTP request and normalize the JSON. Endpoints call `runnable_case_law.ainvoke(...)` and `runnable_dockets.ainvoke(...)` so all CourtListener access goes through LangChain runnables.

**How it calls CourtListener:** Each runnable calls `https://www.courtlistener.com/api/rest/v4/search/` with `Authorization: Token <COURTLISTENER_API_TOKEN>`. Case-law uses `?q=...&type=o`; dockets use `?q=...&type=r`. Responses are normalized to a simple JSON shape for the agent.

## Environment

Set `COURTLISTENER_API_TOKEN` (get a token from [CourtListener API help](https://www.courtlistener.com/help/api/rest/#your-authorization-token)).

## Run

**If you get 404 on `GET /`:** The process on port 8001 may be an old MCP instance. Stop it (Ctrl+C in the terminal where it’s running, or `lsof -i :8001` then `kill <PID>`), then start the MCP again so the app with the root route and request logging is the one on 8001.

**Option A (recommended)** – from repo root, run the script (it will `chdir` into `mcp-server` and start uvicorn):

```bash
# From repo root
pip install -r ../requirements.txt
# Set COURTLISTENER_API_TOKEN in .env or export
python mcp-server/main.py
```

**Option B** – from inside `mcp-server`:

```bash
cd mcp-server
uvicorn main:app --reload --port 8001
```

**Verify MCP is the process on 8001:**  
`curl http://localhost:8001/` should return `{"service":"MCP CourtListener Server","routes":[...]}`. If you get 404, another process is using port 8001—stop it and start the MCP again.

## Endpoints

- `GET /health` — Liveness.
- `GET /search/case-law?q=...&page_size=10` — Search case law (via LangChain runnable).
- `GET /search/dockets?q=...&page_size=10` — Search federal dockets (via LangChain runnable).

## Example requests

```bash
# No auth needed to the MCP; it uses COURTLISTENER_API_TOKEN from env
curl "http://localhost:8001/search/case-law?q=first+amendment"
curl "http://localhost:8001/search/dockets?q=civil+rights"
```
