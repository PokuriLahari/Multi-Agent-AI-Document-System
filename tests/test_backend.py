import asyncio
import pytest
from fastapi.testclient import TestClient
from backend.app.utils.logger import timed_agent, EXECUTION_METRICS
from backend.app.database import SessionLocal, SourceDocument, Job


def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Multi-Agent Document Intelligence" in data["app"]
    assert "timestamp" in data


def test_hello_endpoint_default(client: TestClient):
    response = client.get("/api/hello")
    assert response.status_code == 200
    data = response.json()
    assert "Hello, World!" in data["message"]
    assert data["sprint"] == "Sprint 0 - Skeleton & Foundations"


def test_hello_endpoint_custom_name(client: TestClient):
    response = client.get("/api/hello?name=Alice")
    assert response.status_code == 200
    data = response.json()
    assert "Hello, Alice!" in data["message"]


def test_timed_agent_decorator_sync():
    initial_count = len(EXECUTION_METRICS)

    @timed_agent("MockSyncAgent")
    def compute(x, y):
        return x + y

    result = compute(3, 4)
    assert result == 7
    assert len(EXECUTION_METRICS) == initial_count + 1
    last_metric = EXECUTION_METRICS[-1]
    assert last_metric["agent"] == "MockSyncAgent"
    assert last_metric["function"] == "compute"
    assert last_metric["status"] == "SUCCESS"
    assert last_metric["latency_ms"] >= 0.0


@pytest.mark.asyncio
async def test_timed_agent_decorator_async():
    initial_count = len(EXECUTION_METRICS)

    @timed_agent("MockAsyncAgent")
    async def compute_async(val):
        await asyncio.sleep(0.01)
        return val * 2

    res = await compute_async(10)
    assert res == 20
    assert len(EXECUTION_METRICS) == initial_count + 1
    last_metric = EXECUTION_METRICS[-1]
    assert last_metric["agent"] == "MockAsyncAgent"
    assert last_metric["function"] == "compute_async"
    assert last_metric["status"] == "SUCCESS"
    assert last_metric["latency_ms"] >= 9.0


def test_metrics_endpoint(client: TestClient):
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "metrics" in data
    assert isinstance(data["metrics"], list)


def test_database_models():
    session = SessionLocal()
    try:
        doc = SourceDocument(
            id="doc-test-1",
            filename="sample.pdf",
            file_type="pdf",
            file_size=1024,
            status="pending",
            chunk_count=0
        )
        session.add(doc)
        session.commit()

        retrieved = session.query(SourceDocument).filter_by(id="doc-test-1").first()
        assert retrieved is not None
        assert retrieved.filename == "sample.pdf"
        assert retrieved.file_type == "pdf"

        # Cleanup
        session.delete(retrieved)
        session.commit()
    finally:
        session.close()
