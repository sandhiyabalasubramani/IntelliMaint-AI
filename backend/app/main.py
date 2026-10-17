"""
IntelliMaint AI — FastAPI REST Application Entrypoint

Exposes REST APIs for Machine Registry, Telemetry Ingestion,
ML-Driven Failure Risk Prediction, Maintenance Work Orders, and Fleet Analytics.
"""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.routers import (
    health,
    machines,
    telemetry,
    predictions,
    maintenance,
    analytics,
)

# Logging configuration
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("intellimaint.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    logger.info("Initializing IntelliMaint AI database tables...")
    try:
        init_db()
    except Exception as e:
        logger.error(f"Error during database startup: {e}")
    yield
    # Shutdown
    logger.info("IntelliMaint AI backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Industrial Predictive Maintenance REST API powered by machine learning, "
        "physics-grounded telemetry feature engineering, and automated maintenance planning."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Top-level Health check endpoint
app.include_router(health.router)

# API v1 Router prefix mounting
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(machines.router, prefix=settings.API_V1_PREFIX)
app.include_router(telemetry.router, prefix=settings.API_V1_PREFIX)
app.include_router(predictions.router, prefix=settings.API_V1_PREFIX)
app.include_router(maintenance.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root access to interactive API documentation."""
    return RedirectResponse(url="/docs")
