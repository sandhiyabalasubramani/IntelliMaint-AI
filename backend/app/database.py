"""
IntelliMaint AI — Database Configuration & Session Management

Provides SQLAlchemy 2.x engine, connection pooling, Base declarative model,
and database session lifecycle management for SQLite and PostgreSQL.
"""

from __future__ import annotations
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import settings

logger = logging.getLogger("intellimaint.database")

# Database URL configuration
db_url = settings.DATABASE_URL

# SQLite specific connect_args
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    logger.info(f"Using SQLite database engine at: {db_url}")
else:
    logger.info(f"Using PostgreSQL database engine at: {db_url.split('@')[-1] if '@' in db_url else db_url}")

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

if db_url.startswith("sqlite"):
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Rolls back automatically upon unhandled exception and closes the session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates all database tables defined in SQLAlchemy models."""
    # Import models so that they are registered on the metadata
    import backend.app.models.machine
    import backend.app.models.telemetry
    import backend.app.models.prediction
    import backend.app.models.maintenance

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
