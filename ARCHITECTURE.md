# Architecture Overview

## High-level flow

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│  Frontend       │────▶│  LLM Agent Backend   │────▶│  MCP Server     │────▶│  Third-Party API    │
│  (Web UI)       │     │  (LangChain + tools) │     │  (API wrapper)   │     │  (CourtListener)    │
└─────────────────┘     └──────────────────────┘     └─────────────────┘     └─────────────────────┘
        ▲                            │                          │
        │                            │                          │
        └────────────────────────────┴──────────────────────────┘
                     JSON responses (user-facing)
```

- **Frontend**: User enters a natural-language query; receives and displays the agent’s response.
- **Agent Backend**: Interprets intent, selects tools, calls the MCP Server via HTTP, and formats answers.
- **MCP Server**: Wraps the third-party API; exposes a small set of endpoints and normalizes responses.
- **Third-Party API**: CourtListener (legal search: case law and federal dockets); token authentication required.

## Separation of concerns

| Layer           | Responsibility                                      | Does not |
|----------------|------------------------------------------------------|----------|
| Frontend       | UI, sending user message, rendering response         | Call MCP or third-party API directly |
| Agent Backend  | LangChain ChatOpenAI, bind_tools, messages, tool loop | Store third-party API keys; parse raw CourtListener JSON |
| MCP Server     | LangChain runnables (RunnableLambda) for CourtListener fetch + normalize | Contain LLM logic or frontend code   |

## Security

- **API keys**: Third-party and LLM keys are read from environment variables (e.g. `.env`); never committed. See `.env.example`.
- **MCP Server**: Runs on localhost or internal network; frontend talks only to the Agent Backend.
- **Agent Backend**: Single entry point for the app; validates and forwards only to the MCP Server.

## Tech stack

- **MCP Server**: Python, FastAPI, LangChain (`RunnableLambda` for CourtListener fetch/normalize), `httpx`.
- **Agent Backend**: Python, FastAPI, LangChain (`ChatOpenAI`, `bind_tools`, `SystemMessage`/`HumanMessage`/`ToolMessage`), model gpt-5-mini-2025-08-07.
- **Frontend**: React (Vite), fetch to Agent Backend.
