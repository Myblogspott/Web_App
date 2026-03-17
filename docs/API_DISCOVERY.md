# API Selection and Discovery

## Chosen API: CourtListener

**Core function:** Search case law, federal dockets, judges, and oral arguments via the CourtListener Legal Search API.

- **Base URL:** `https://www.courtlistener.com/api/rest/v4`
- **Authentication:** Token required. Header: `Authorization: Token <your-token>`.
- **Obtaining a token:** Sign in at [CourtListener](https://www.courtlistener.com/sign-in/), then view your token in the [API help section](https://www.courtlistener.com/help/api/rest/#your-authorization-token).
- **Rate limits:** Throttling applies; use responsibly. No per-query tracking per privacy policy.
- **Documentation:** [REST API v4](https://www.courtlistener.com/help/api/rest/), [Legal Search API](https://courtlistener.com/help/api/rest/search).

### Main endpoints used by MCP Server

| Operation       | CourtListener endpoint     | MCP exposes           | Description                          |
|----------------|----------------------------|------------------------|--------------------------------------|
| Case law search| `GET /search/?q=...&type=o`| `GET /search/case-law` | Search opinions/clusters (case law). |
| Docket search  | `GET /search/?q=...&type=r`| `GET /search/dockets`  | Search federal court dockets.        |

### Search parameters

- **q** (required): Search query; supports [advanced operators](https://courtlistener.com/help/search-operators/).
- **type**: `o` = case law (opinion clusters), `r` = federal dockets (with up to 3 docs). Default in API is case law.
- **page_size**: Number of results (cursor-based pagination). We use a small default (e.g. 5–10) for agent responses.

### Response shape (normalized by MCP)

- **Case law:** List of `{ "case_name", "court", "date_filed", "snippet", "citations", "url" }`.
- **Dockets:** List of `{ "case_name", "court", "docket_number", "snippet", "url" }` (simplified).

### Note for video

CourtListener provides the **core function** of the app: **legal search** (case law and federal dockets). The MCP Server wraps it so the LLM agent can run searches without handling auth or raw API parameters.
