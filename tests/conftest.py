import os
import pytest
from fastapi.testclient import TestClient

# Ensure test environment uses a test SQLite database
os.environ["DATABASE_URL"] = "sqlite:///./test_doc_intel.db"

from backend.app.main import app
from backend.app.database import Base, engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_doc_intel.db"):
        try:
            os.remove("test_doc_intel.db")
        except OSError:
            pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
