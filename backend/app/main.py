from contextlib import asynccontextmanager
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import init_db, get_db
from backend.app.utils.logger import get_logger, timed_agent, EXECUTION_METRICS

logger = get_logger("API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite database tables...")
    init_db()
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutdown.")


app = FastAPI(
    title="Multi-Agent Document Intelligence API",
    version="0.1.0",
    description="Backend API for Multi-Agent Document Intelligence System",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@timed_agent("SystemAgent")
def sample_health_check_work():
    """Simulated internal check to verify timed_agent decorator."""
    return True


@app.get("/api/health")
def health_check():
    sample_health_check_work()
    return {
        "status": "ok",
        "app": "Multi-Agent Document Intelligence System",
        "version": "0.1.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.get("/api/hello")
def hello_endpoint(name: str = "World"):
    return {
        "message": f"Hello, {name}! Multi-Agent Document Intelligence System is ready.",
        "sprint": "Sprint 0 - Skeleton & Foundations",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.get("/api/metrics")
def get_metrics():
    """Observability endpoint: inspect per-agent call timings."""
    return {
        "total_calls": len(EXECUTION_METRICS),
        "metrics": EXECUTION_METRICS[-50:]  # Return latest 50 metrics
    }
