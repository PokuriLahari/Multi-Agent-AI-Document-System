# Non-Functional Requirements (NFR) Specification

## Project: Multi-Agent AI Document Intelligence System

---

## NFR-01 — Performance
- **Description:** The system shall measure, record, and optimize latency across all operational stages:
  - **API Response Latency:** Lightweight metadata/health endpoints shall respond in under 100 ms (Sprint 0 baseline: ~10 ms).
  - **Document Processing Time:** Text extraction and chunking shall process at a rate exceeding 10 pages per second for standard text documents.
  - **Retrieval Latency:** Vector similarity search over an embedded collection of up to 10,000 chunks shall return top-$k$ results within 200 ms.
  - **Agent Execution Latency:** Per-agent latency must be tracked and recorded per invocation via `@timed_agent`.
- **Measurement:** Instrumented via Python `time.perf_counter()` inside the `@timed_agent` decorator, exposed via `/api/metrics`.

---

## NFR-02 — Reliability
- **Description:** The system shall maintain high operational availability and robustness:
  - Gracefully handle malformed or empty user queries without application crash.
  - Isolate agent exceptions so a failure in one agent (e.g., summarizer timeout) returns a structured error message rather than terminating the FastAPI server.
  - Track document processing lifecycle in SQLite (`pending`, `processing`, `indexed`, `failed`) with recorded error messages.
- **Measurement:** Monitored via HTTP 4xx/5xx error rates and job status audit in the SQLite `jobs` table.

---

## NFR-03 — AI Reliability / Groundedness
- **Description:** The system shall enforce rigorous grounding and hallucination prevention:
  - All factual claims in answers must trace directly to retrieved chunk text.
  - System must attach source evidence (file, page/section, verbatim snippet) to all answers.
  - Explicitly refuse to answer queries when retrieval relevance score is below confidence threshold ($T_{sim} < 0.65$).
- **Status:** Planned for implementation in Sprint 2 (Core RAG Loop).

---

## NFR-04 — Security
- **Description:** The system shall implement defense-in-depth for document and data handling:
  - Enforce maximum upload file size (default: 25 MB) and reject files exceeding limit.
  - Whitelist allowed MIME types and file extensions (`.pdf`, `.docx`, `.pptx`, `.txt`, `.csv`). Reject executable or arbitrary binaries.
  - Zero hardcoded secrets: All API keys (e.g., Anthropic, OpenAI) and connection strings must reside in `.env` and be loaded via `pydantic-settings`.
  - Prevent sensitive credentials and tokens from leaking into application logs or client error payloads.

---

## NFR-05 — Privacy
- **Description:** The system shall safeguard user document privacy:
  - Document contents are stored locally on the host machine (`uploads/` and embedded `.vector_store/` or ChromaDB directory).
  - Avoid dumping raw document text into console logs or persistent server debug logs.
  - Only the retrieved chunk snippets required for an individual query are forwarded to external LLMs; irrelevant document sections are never transmitted.

---

## NFR-06 — Usability
- **Description:** The system shall provide an intuitive, transparent user experience:
  - Streamlit frontend must clearly indicate backend connectivity state, model readiness, and upload progress.
  - Show responsive loading indicators (spinners, progress bars) during document chunking and vector indexing.
  - Provide human-readable error descriptions rather than raw stack traces.
  - Encapsulate agent orchestration details behind a simple, unified chat interface.

---

## NFR-07 — Scalability
- **Description:** The system architecture shall support growing document workloads without premature architectural complexity:
  - Support incremental ingestion of hundreds of documents without requiring full vector re-indexing.
  - Background task execution via FastAPI background tasks or dedicated async worker queue.
  - Maintain a lightweight footprint (SQLite + embedded ChromaDB) without requiring external heavy distributed services (no Kafka, Redis, or Kubernetes unless specifically justified by enterprise scale requirements).

---

## NFR-08 — Maintainability
- **Description:** The codebase shall adhere to clean software engineering and single-responsibility principles:
  - Decoupled layers: API (`backend/app/main.py`), Agents (`backend/app/agents/`), Models (`backend/app/models/`), Utilities (`backend/app/utils/`), and UI (`frontend/app.py`).
  - Centralized configuration via `backend/app/config.py` using `pydantic-settings`.
  - Modular parser architecture allowing support for new document types without refactoring existing parsers.
  - Automated test coverage running via `pytest` to prevent regressions.

---

## NFR-09 — Observability
- **Description:** The system shall deliver end-to-end diagnostic visibility:
  - Standardized structured logging format: `timestamp | level | agent/module | message`.
  - Continuous measurement of per-agent function latency via `@timed_agent`.
  - Queryable in-memory and API metrics endpoint (`/api/metrics`) reporting execution latency, status (`SUCCESS` / `FAILED`), and call volume.

---

## NFR-10 — Testability
- **Description:** The project shall support automated verification across all levels:
  - **Unit Tests:** Fast execution testing chunking algorithms, config loading, and decorator mechanics.
  - **API Tests:** Fast HTTP tests verifying status codes, JSON schema validation, and health/metrics endpoints.
  - **Database Tests:** Verification of SQLite schema initialization, model CRUD operations, and session lifecycle.
  - **CI Automation:** Continuous testing in GitHub Actions on every pull request and push to `main`.

---

## NFR-11 — Compatibility & Reproducibility
- **Description:** The project shall ensure reproducible setup across developer environments:
  - Pinned, well-defined dependencies in `requirements.txt`.
  - Configuration template provided in `.env.example`.
  - Documented startup commands for backend (`uvicorn`), frontend (`streamlit`), and tests (`pytest`).
  - Fully compatible with Python 3.10 through 3.13 on Windows, macOS, and Linux.

---

## NFR-12 — Recoverability
- **Description:** The system shall maintain state consistency during failures:
  - If a document fails during chunking or indexing, its status is flagged as `failed` with the error reason recorded in the database; previously indexed documents remain intact.
  - Vector index operations shall be atomic per document collection to avoid partial, corrupted vector states.
