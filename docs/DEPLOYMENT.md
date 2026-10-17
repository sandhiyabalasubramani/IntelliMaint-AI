# IntelliMaint AI — Setup and Deployment Guide

This guide covers local development and the checks required before publishing a hosted demo. Hosting providers and service plans change; verify current provider-specific settings before deployment.

## Architecture

- **Frontend:** Streamlit, launched from `frontend/app.py` on port 8501.
- **API:** FastAPI, launched from `backend.app.main:app` on port 8000.
- **Persistence:** SQLite for local development; PostgreSQL can be configured through `DATABASE_URL`.
- **ML:** Model artifact and metadata are stored under `ml/models/`.

## Local Setup

### 1. Create an environment

Python 3.13 is used by the automated CI workflow.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env`. Review `APP_ENV`, `DEBUG`, `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, and the frontend API URL. Do not commit the real `.env` file.

### 3. Start the backend

In terminal 1:

```bash
python scripts/run_backend.py
```

Confirm the backend health endpoint responds at `http://127.0.0.1:8000/health`. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

### 4. Start the frontend

In terminal 2:

```bash
python scripts/run_frontend.py
```

Open `http://127.0.0.1:8501`.

### 5. Run automated tests

```bash
python -m pytest
```

The GitHub Actions workflow runs this test command for pushes and pull requests to `main`.

## Hosted Demo Planning

A public deployment normally requires separate frontend and backend services. Configure the frontend's API base URL to the reachable deployed API URL, not to `127.0.0.1` or `localhost`. Those addresses refer to the current machine/container and will not reach a separate hosted service.

Before publishing:
- Configure production environment variables in the hosting provider's secret settings.
- Use a managed database with restricted network access, TLS, backups, and a tested restore process.
- Set CORS to the exact public frontend origin(s).
- Confirm model files and runtime dependencies are included in the deployed artifact.
- Confirm the health endpoint, API routes, CSV upload, prediction history, maintenance work orders, analytics, and PDF generation work after deployment.
- Check provider logs for errors without exposing credentials or sensitive telemetry.
- Run the end-to-end checklist in [Production Readiness](PRODUCTION_READINESS.md).

## Important Limitations

This is an educational and portfolio project, not a certified industrial safety system. The included benchmark dataset and model may not represent a specific factory, machine, sensor, or operating environment. Validate the model on representative, independently collected data and involve qualified engineers before operational use. Never use unvalidated predictions as the sole basis for safety-critical decisions.
