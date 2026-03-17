# Agent Backend

LangChain-based agent with tool calling against the MCP Server (CourtListener wrapper). Exposes `POST /chat` for the frontend. Uses **gpt-5-mini-2025-08-07** only (no GPT-4).

## LangChain usage

- **ChatOpenAI** (`langchain_openai`): LLM with `model="gpt-5-mini-2025-08-07"`, `temperature=0`.
- **bind_tools**: Tools are bound via `llm.bind_tools(TOOLS)` for OpenAI function/tool calling.
- **Tools** (`langchain_core.tools.tool`): `search_case_law` and `search_dockets` are `@tool`-decorated functions that call the MCP Server over HTTP and return JSON strings.
- **Messages**: `SystemMessage`, `HumanMessage`, `AIMessage`, and `ToolMessage` from `langchain_core.messages` build the conversation; each assistant `tool_calls` turn is followed by one `ToolMessage` per `tool_call_id` (OpenAI requirement).
- **Conversation memory**: The chat API accepts an optional `history` of prior turns (`{ "role": "user"|"assistant", "content": "..." }`). The model receives `[SystemMessage, ...history, HumanMessage(current)]` so it can refer to earlier questions and answers (OpenAI/LangChain pattern). History is capped at the last 20 messages to stay within context limits.
- **Agent loop**: Manual ReAct-style loop: invoke LLM → if `tool_calls`, append assistant message and one `ToolMessage` per call → invoke again until the model returns text only.

## Environment

- `OPENAI_API_KEY` (required)
- `MCP_SERVER_URL` (optional, default `http://localhost:8001`)

## Run

```bash
# From repo root: ensure MCP Server is running on 8001 and COURTLISTENER_API_TOKEN is set
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

## API

- `GET /health` — Liveness.
- `POST /chat` — Body: `{ "message": "Find case law on first amendment free speech", "history": [{"role":"user","content":"..."},{"role":"assistant","content":"..."}] }` (optional `history` for conversation memory). Returns `{ "response": "..." }`.

## Tool definitions

- **search_case_law(query)** — Calls MCP `GET /search/case-law` for court opinions.
- **search_dockets(query)** — Calls MCP `GET /search/dockets` for federal dockets.

The system prompt instructs the LLM to choose the appropriate tool (case law vs dockets) and to summarize results with case name, court, date, snippet, and URL.
