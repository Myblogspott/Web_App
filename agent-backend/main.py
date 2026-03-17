"""
LLM Agent Backend: LangChain agent with tool calling against the MCP Server (CourtListener).
Uses LangChain (ChatOpenAI, bind_tools) with gpt-5-mini-2025-08-07. No GPT-4.
"""
import json
import logging
import os
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MCP_BASE = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

# Model: gpt-5-mini-2025-08-07 only (no GPT-4)
MODEL_NAME = "gpt-5-mini-2025-08-07"


# --- LangChain tools that call MCP Server (CourtListener wrapper) ---

@tool
def search_case_law(
    query: Annotated[str, "Search query for case law (e.g. 'first amendment free speech', 'employment discrimination')"],
) -> str:
    """Search case law (court opinions). Use when the user asks about court cases, opinions, precedents, or legal decisions."""
    try:
        r = httpx.get(
            f"{MCP_BASE}/search/case-law",
            params={"q": query.strip(), "page_size": 8},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def search_dockets(
    query: Annotated[str, "Search query for federal dockets (e.g. case name, party, docket number)"],
) -> str:
    """Search federal court dockets (PACER). Use when the user asks about dockets, federal cases, or case filings."""
    try:
        r = httpx.get(
            f"{MCP_BASE}/search/dockets",
            params={"q": query.strip(), "page_size": 8},
            timeout=15.0,
        )
        r.raise_for_status()
        data = r.json()
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})


TOOLS = [search_case_law, search_dockets]

SYSTEM_PROMPT = """You are a helpful legal research assistant. You have access to CourtListener via two tools:

- search_case_law: Search court opinions and case law. Use for questions about legal decisions, precedents, case law, or "find cases about X".
- search_dockets: Search federal court dockets. Use for questions about dockets, federal case filings, or "find docket for X".

Choose the tool that best matches the user's question. Summarize results clearly: case name, court, date (if relevant), and a short snippet. Include the URL when available. Do not make up citations or cases; only report what the search returned."""


# Max conversation turns to include in context (user + assistant pairs) to stay within model context
MAX_HISTORY_MESSAGES = 20


def _run_agent(user_message: str, history: list[dict] | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    llm = ChatOpenAI(model=MODEL_NAME, temperature=0, api_key=api_key)
    llm_with_tools = llm.bind_tools(TOOLS)

    # Build message list: system + conversation history + current user message (OpenAI/LangChain pattern)
    messages: list = [SystemMessage(content=SYSTEM_PROMPT)]
    if history:
        for entry in history[-MAX_HISTORY_MESSAGES:]:
            role = (entry.get("role") or "").strip().lower()
            content = (entry.get("content") or "").strip()
            if not content and role != "assistant":
                continue
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_message))
    tool_map = {t.name: t for t in TOOLS}
    max_steps = 5

    for _ in range(max_steps):
        response = llm_with_tools.invoke(messages)
        if not response.tool_calls:
            return (response.content or "").strip() or "I couldn't generate a response."

        # Build a minimal AIMessage with only tool_calls we will respond to (same ids as ToolMessages).
        # LangChain can merge tool_calls from content blocks when converting to OpenAI; using a clean
        # AIMessage with plain string content and explicit tool_calls avoids extra/duplicate ids.
        clean_tool_calls = []
        for tc in response.tool_calls:
            raw_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
            tid = str(raw_id) if raw_id is not None else ""
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}) or {}
            clean_tool_calls.append({"id": tid, "name": name, "args": args})
        content = response.content
        if isinstance(content, list):
            content = ""  # avoid content blocks that could add more tool_calls on conversion
        clean_ai = AIMessage(content=content or "", tool_calls=clean_tool_calls)
        messages.append(clean_ai)

        # One ToolMessage per tool_call (OpenAI requires every tool_call_id to have a response)
        for i, tc in enumerate(response.tool_calls):
            tool_call_id = clean_tool_calls[i]["id"]
            name = clean_tool_calls[i]["name"]
            args = clean_tool_calls[i]["args"]
            if name in tool_map:
                result = tool_map[name].invoke(args)
            else:
                result = json.dumps({"error": f"Unknown tool: {name}"})
            messages.append(ToolMessage(content=result, tool_call_id=tool_call_id))

        # Next turn: model consumes tool results and may return text or more tool_calls
        response = llm_with_tools.invoke(messages)
        if not response.tool_calls:
            return (response.content or "").strip() or "Done."
        # If we get more tool_calls, process them in the next loop iteration (append clean AI + tool msgs)

    return "I hit the step limit; please try a more focused question."


class ChatHistoryEntry(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=0, max_length=50000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatHistoryEntry] | None = Field(default_factory=list, max_length=50)


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        history = [h.model_dump() for h in (req.history or [])]
        response_text = _run_agent(req.message, history=history)
        return ChatResponse(response=response_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="CourtListener search timed out")
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Cannot reach MCP Server. Is it running on port 8001?",
        )
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
