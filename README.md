# Multi-Agent AI Document Intelligence System

A modular, multi-agent document intelligence platform built with **FastAPI**, **Streamlit**, and **SQLite**, designed around single-responsibility agents for parsing, retrieving, and reasoning across complex multi-format documents (PDF, DOCX, PPTX, TXT, CSV) with full citation grounding and honest evidence refusal.

---

## 📍 Current Sprint

**Sprint 0 — Engineering Foundation**

Sprint 0 establishes the engineering bedrock: repository layout, formal functional/non-functional requirements, architectural blueprints, development environment setup, database foundation, structured observability, automated testing framework, CI pipeline, and Git workflow.

---

## 🏗️ Architecture

The system decouples the presentation layer, REST API, autonomous agents, and persistent storage:

- **Streamlit Frontend (Port 8501):** Interactive user dashboard providing connection health status, query execution, and real-time observability telemetry.
- **FastAPI Backend (Port 8000):** High-performance API server managing agent invocation, request routing, and lifecycle events.
- **Autonomous Agents:** Plain Python classes adhering to single-responsibility principles (Orchestrator, Ingestion, Retrieval, QA, Summarization, Explanation, Comparison, Extraction, Generation).
- **SQLite Database:** Transactional storage managing source document metadata, job processing states, and session audit history.
- **ChromaDB Vector Store:** Embedded vector store providing semantic similarity search over document chunks.

For comprehensive architectural specifications and diagrams, see [docs/architecture.md](docs/architecture.md).

---

## 📚 Requirements & Documentation

- [docs/requirements.md](docs/requirements.md) — Detailed Functional Requirements (FR-01 through FR-15).
- [docs/nfr.md](docs/nfr.md) — Non-Functional Requirements with measurable quality targets (NFR-01 through NFR-12).
- [docs/traceability.md](docs/traceability.md) — Requirements Traceability Matrix (RTM) tracking components, tests, and sprints.
- [docs/architecture.md](docs/architecture.md) — System architecture specifications, Mermaid diagram, and database strategy.
- [docs/git-workflow.md](docs/git-workflow.md) — Branching conventions, pull request lifecycle, and commit standards.
- [docs/sprint-0-report.md](docs/sprint-0-report.md) — Sprint 0 verification report, live metrics, and limitations.

---

## 🚀 Development Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11 & 3.13)
- `pip` or `uv`

### 2. Environment Setup
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```
or with `uv`:
```bash
uv pip install -r requirements.txt
```

Copy the environment template:
```bash
copy .env.example .env
```

---

## 🏃 Running the Application

### 1. Start the FastAPI Backend
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation will be accessible at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start the Streamlit Frontend
In a separate terminal:
```bash
streamlit run frontend/app.py
```
The user interface will open at: [http://localhost:8501](http://localhost:8501)

### 3. Run Automated Tests
```bash
pytest -v
```

---

## 📊 Current Implementation Status

### ✅ Implemented (Sprint 0 Foundation)
- **Repository Structure & Clean Layering:** Separation of API, frontend, models, services, utilities, and tests.
- **FastAPI Core:** Health (`/api/health`), hello test (`/api/hello`), and metrics (`/api/metrics`) endpoints.
- **Streamlit Frontend:** Live connection status card, greeting round-trip test, and execution metrics table.
- **Database Foundation:** SQLite setup with `SourceDocument` and `Job` SQLAlchemy models.
- **Configuration Management:** Centralized settings via `pydantic-settings` with `.env` support.
- **Observability & Latency Tracking:** Structured logging and `@timed_agent` decorator tracking execution latency.
- **Testing Framework:** Pytest test suite covering endpoints, database models, and sync/async decorators (7 passing).
- **GitHub Actions CI:** Automated workflow executing test suite across branches on push and pull requests.
- **Comprehensive Documentation:** Requirements, NFRs, Traceability Matrix, Architecture, Git Workflow, and Sprint Report.

### ⏳ Planned (Sprint 1+)
- **Sprint 1:** Multi-format document ingestion (PDF, DOCX, PPTX, TXT, CSV), text chunking, and ChromaDB vector indexing.
- **Sprint 2:** Core RAG pipeline, QAAgent, citation attribution, and honest refusal on insufficient evidence.
- **Sprint 3:** Orchestrator intent routing, SummarizationAgent, and ExplanationAgent.
- **Sprint 4:** ComparisonAgent and ExtractionAgent (structured JSON schemas).
- **Sprint 5:** GenerationAgent, multi-source cross-document synthesis, and conversational MemoryManager.
- **Sprint 6:** Source lifecycle management UI, async progress tracking, and full integration polish.
