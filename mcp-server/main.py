"""
MCP Server: LangChain-wrapped CourtListener Legal Search API.
Uses LangChain runnables (RunnableLambda) to fetch and normalize CourtListener responses.
Exposes normalized search endpoints for the LLM agent backend.
"""
import logging
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_core.runnables import RunnableLambda

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP CourtListener Server", version="1.0.0")


@app.middleware("http")
async def log_requests(request, call_next):
    """Log every request so you can see MCP being hit in the MCP terminal."""
    logger.info("MCP request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("MCP response: %s %s -> %s", request.method, request.url.path, response.status_code)
    return response


COURTLISTENER_BASE = "https://www.courtlistener.com/api/rest/v4"
CL_TOKEN = os.getenv("COURTLISTENER_API_TOKEN")


def _auth_headers() -> dict[str, str]:
    if not CL_TOKEN or not CL_TOKEN.strip():
        raise HTTPException(
            status_code=503,
            detail="COURTLISTENER_API_TOKEN is not set. Get a token at https://www.courtlistener.com/help/api/rest/",
        )
    return {"Authorization": f"Token {CL_TOKEN.strip()}"}


# --- LangChain runnables: CourtListener fetch + normalize ---

async def _fetch_case_law_impl(inputs: dict[str, Any]) -> dict[str, Any]:
    """LangChain runnable input: { query, page_size }. Fetches CourtListener search type=o and normalizes."""
    q = (inputs.get("query") or inputs.get("q") or "").strip()
    page_size = inputs.get("page_size", 10)
    params = {"q": q, "type": "o", "page_size": page_size}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{COURTLISTENER_BASE}/search/",
            params=params,
            headers=_auth_headers(),
        )
        r.raise_for_status()
    data = r.json()
    count = data.get("count", 0)
    raw_results = data.get("results") or []
    base_url = "https://www.courtlistener.com"
    results = []
    for item in raw_results:
        opinions = item.get("opinions") or []
        snippet = ""
        if opinions:
            snippet = (opinions[0].get("snippet") or "").strip()[:500]
        if not snippet:
            snippet = (item.get("snippet") or "")[:500]
        results.append({
            "case_name": item.get("caseName") or item.get("caseNameFull") or "Unknown",
            "court": item.get("court") or "",
            "date_filed": item.get("dateFiled"),
            "snippet": snippet,
            "citations": item.get("citation") or [],
            "url": base_url + item.get("absolute_url", "") if item.get("absolute_url") else "",
        })
    return {"count": count, "results": results}


async def _fetch_dockets_impl(inputs: dict[str, Any]) -> dict[str, Any]:
    """LangChain runnable input: { query, page_size }. Fetches CourtListener search type=r and normalizes."""
    q = (inputs.get("query") or inputs.get("q") or "").strip()
    page_size = inputs.get("page_size", 10)
    params = {"q": q, "type": "r", "page_size": page_size}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{COURTLISTENER_BASE}/search/",
            params=params,
            headers=_auth_headers(),
        )
        r.raise_for_status()
    data = r.json()
    count = data.get("count", 0)
    raw_results = data.get("results") or []
    base_url = "https://www.courtlistener.com"
    results = []
    for item in raw_results:
        snippet = (item.get("snippet") or "")[:500]
        results.append({
            "case_name": item.get("caseName") or item.get("caseNameFull") or "Unknown",
            "court": item.get("court") or "",
            "docket_number": item.get("docketNumber"),
            "snippet": snippet,
            "url": base_url + item.get("absolute_url", "") if item.get("absolute_url") else "",
        })
    return {"count": count, "results": results}


# LangChain runnables used by the MCP endpoints
runnable_case_law = RunnableLambda(_fetch_case_law_impl)
runnable_dockets = RunnableLambda(_fetch_dockets_impl)


# --- Pydantic response models ---

class CaseLawResult(BaseModel):
    case_name: str
    court: str
    date_filed: str | None
    snippet: str
    citations: list[str]
    url: str


class CaseLawSearchResponse(BaseModel):
    count: int
    results: list[CaseLawResult]


class DocketResult(BaseModel):
    case_name: str
    court: str
    docket_number: str | None
    snippet: str
    url: str


class DocketSearchResponse(BaseModel):
    count: int
    results: list[DocketResult]


@app.get("/")
def root() -> dict:
    """Identify this server; use GET /health for liveness."""
    return {
        "service": "MCP CourtListener Server",
        "routes": ["/health", "/search/case-law", "/search/dockets"],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search/case-law", response_model=CaseLawSearchResponse)
async def search_case_law(
    q: str = Query(..., min_length=1, max_length=500),
    page_size: int = Query(10, ge=1, le=20),
) -> CaseLawSearchResponse:
    """Search case law via LangChain runnable (CourtListener type=o)."""
    try:
        out = await runnable_case_law.ainvoke({"query": q, "page_size": page_size})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=502, detail="CourtListener authentication failed. Check COURTLISTENER_API_TOKEN.")
        logger.warning("CourtListener error: %s", e.response.text)
        raise HTTPException(status_code=502, detail="CourtListener search error")
    except httpx.RequestError as e:
        logger.warning("CourtListener request error: %s", e)
        raise HTTPException(status_code=503, detail="CourtListener unavailable")
    return CaseLawSearchResponse(**out)


@app.get("/search/dockets", response_model=DocketSearchResponse)
async def search_dockets(
    q: str = Query(..., min_length=1, max_length=500),
    page_size: int = Query(10, ge=1, le=20),
) -> DocketSearchResponse:
    """Search federal dockets via LangChain runnable (CourtListener type=r)."""
    try:
        out = await runnable_dockets.ainvoke({"query": q, "page_size": page_size})
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=502, detail="CourtListener authentication failed. Check COURTLISTENER_API_TOKEN.")
        logger.warning("CourtListener error: %s", e.response.text)
        raise HTTPException(status_code=502, detail="CourtListener search error")
    except httpx.RequestError as e:
        logger.warning("CourtListener request error: %s", e)
        raise HTTPException(status_code=503, detail="CourtListener unavailable")
    return DocketSearchResponse(**out)


if __name__ == "__main__":
    import uvicorn
    # Run from this file's directory so "main:app" resolves to this module when using reload
    _dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(_dir)
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
