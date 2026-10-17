"""
IntelliMaint AI — Pytest Configuration & Test Fixtures
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.machine import Machine
from backend.app.models.maintenance import MaintenanceTask
from backend.app.models.prediction import PredictionRecord

# Use an isolated, in-memory SQLite database with StaticPool for fast, isolated test execution
TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

from sqlalchemy import event
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh database session for each test, rolling back changes upon completion."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency pointing to the isolated test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_machine(db_session):
    """Fixture providing a registered test machine."""
    m = Machine(
        machine_id="TEST-MILL-01",
        name="Test 5-Axis CNC Mill",
        machine_type="CNC Milling Machine",
        department="Test Bay Alpha",
        manufacturer="Haas Automation",
        installation_date="2023-01-01",
        operational_status="OPERATIONAL",
        notes="Automated test fixture machine",
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m
