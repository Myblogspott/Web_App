## Agentic Developer Project – Phase Plan V1.0

### Overview
This plan breaks the Agentic Developer Project into clear, sequential phases, aligned with the deliverables and evaluation criteria in `Agentic Developer Project.pdf`.

### Phase 1 – Discovery & API Selection
- **Objectives**
  - Select a suitable public REST API with free access (e.g., Weather, Jokes, Facts, Public Data).
  - Understand its authentication model, rate limits, and core endpoints.
- **Key Tasks**
  - Shortlist 2–3 candidate APIs that are simple, reliable, and well-documented.
  - Compare APIs on data usefulness, stability, and complexity of responses.
  - Finalize one API and obtain API keys.
  - Capture notes on core endpoints you plan to expose via the MCP Server.
- **Outputs**
  - One selected API with keys configured locally (e.g., `.env`).
  - Short architectural note describing chosen API and primary use cases.

### Phase 2 – High-Level Architecture & Repo Setup
- **Objectives**
  - Define overall system architecture (Frontend, LLM Agent Backend, MCP Server).
  - Initialize a clean, well-structured repository.
- **Key Tasks**
  - Sketch an architecture diagram showing:
    - Frontend web app → LLM Agent Backend → MCP Server → Third-party API.
  - Decide tech stack (e.g., Python + FastAPI for MCP/Agent, React or Next.js for frontend).
  - Initialize repo with folders:
    - `mcp-server/` (API wrapper)
    - `agent-backend/` (LLM + tool calling)
    - `frontend/` (web UI)
  - Add base dependency files:
    - `requirements.txt` or `pyproject.toml` for Python services.
    - `package.json` for frontend.
  - Create an initial `README.md` with high-level overview and tech choices.
- **Outputs**
  - Repo initialized with clear folder structure.
  - Architecture documented at a high level in `README.md` or a separate `ARCHITECTURE.md`.

### Phase 3 – MCP Server (API Wrapper) Implementation
- **Objectives**
  - Implement an MCP Server (or equivalent microservice) that wraps the chosen REST API.
  - Provide clean, minimal, and well-typed endpoints for the agent backend.
- **Key Tasks**
  - Design API surface exposed by the MCP Server (e.g., `GET /summary`, `GET /search`, etc.).
  - Implement routes that:
    - Handle authentication and API key management securely (env vars).
    - Call the third-party API endpoints.
    - Normalize and simplify API responses for the agent (remove noise).
  - Add error handling, basic logging, and rate-limit awareness.
  - Write at least smoke tests for key endpoints.
- **Outputs**
  - Running MCP Server exposing a small, focused set of endpoints.
  - Basic test coverage and example curl/HTTP requests documented.

### Phase 4 – LLM Agent Backend & Tool Definitions
- **Objectives**
  - Build the LLM Agent backend using LangChain or similar.
  - Define tools/functions that call the MCP Server.
- **Key Tasks**
  - Choose LLM provider and set up API keys.
  - Define tool schemas that mirror MCP endpoints (input/output types).
  - Implement LangChain (or equivalent) chains/agents that:
    - Receive user intent from the frontend.
    - Decide which MCP tools to call and with what parameters.
    - Post-process results into user-friendly responses.
  - Design prompt templates that:
    - Explain the MCP tools and when to use them.
    - Encourage structured, concise answers for the UI.
  - Add minimal unit/integration tests for tool-calling workflows.
- **Outputs**
  - Agent backend service running and successfully calling the MCP Server.
  - Documented tool definitions and example prompts.

### Phase 5 – Frontend Web Application
- **Objectives**
  - Implement a simple, clean UI for interacting with the agent.
  - Support at least one primary user journey end-to-end.
- **Key Tasks**
  - Set up frontend framework (React/Next.js/Vite, etc.).
  - Design UX flow:
    - Input area for user query.
    - Display of agent responses and relevant data from the API.
    - Loading/error states.
  - Implement API client from frontend to LLM Agent Backend.
  - Add basic styling and responsive layout.
  - Include affordances to showcase:
    - The selected API’s core capability.
    - Agent reasoning or intermediate results, if appropriate.
- **Outputs**
  - Frontend that can send a query and display agent output powered by the MCP Server.
  - Screenshots for later use in documentation and video.

### Phase 6 – Integration, Testing & Refinement
- **Objectives**
  - Ensure all components work smoothly together.
  - Polish behavior for reliability and clarity.
- **Key Tasks**
  - Test end-to-end flows:
    - Frontend → Agent Backend → MCP Server → Third-party API → Back to UI.
  - Handle edge cases (empty inputs, API errors, timeouts).
  - Improve prompt engineering based on observed behavior (hallucination reduction, better tool usage).
  - Add logging/observability hooks where helpful.
  - Ensure environment configuration is clear and minimal.
- **Outputs**
  - Stable end-to-end demo path.
  - Updated prompts and error messages for better UX.

### Phase 7 – Documentation & Repo Polish
- **Objectives**
  - Prepare the repository for another developer to pick up quickly.
  - Align documentation with assessment criteria.
- **Key Tasks**
  - Expand `README.md` to include:
    - Setup steps (API keys, env vars, local run commands).
    - How to start MCP Server, Agent Backend, and Frontend.
    - Example usage scenarios.
  - Add sections on:
    - Security considerations (API key handling).
    - Architectural decisions (why this API, why this design).
    - Notes for new contributors.
  - Ensure dependency files (`requirements.txt`, `package.json`) are accurate.
- **Outputs**
  - Production-ready documentation suitable for sharing with a new team member.
  - Clean, navigable repository.

### Phase 8 – Video Demonstration & Final Review
- **Objectives**
  - Produce the required screen recording with on-camera presence.
  - Clearly narrate architecture, prompts, and user experience.
- **Key Tasks**
  - Draft a short script/outline:
    - Introduction and chosen API.
    - Architecture overview (MCP, Agent Backend, Frontend).
    - Walkthrough of prompts and tool definitions.
    - Live demo of key user flows.
    - Deployment discussion (Docker/Kubernetes/Serverless at a conceptual level).
    - Documentation approach and how a new dev would onboard.
  - Record the video (ScreenRec or similar) with yourself on camera.
  - Watch once to ensure clarity and technical accuracy.
- **Outputs**
  - Final video demonstration file.
  - Project ready for submission/review.
