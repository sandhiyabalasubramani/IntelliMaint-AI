# Contributing to IntelliMaint AI

Thank you for helping improve IntelliMaint AI, an educational industrial predictive-maintenance platform.

## Before You Start

1. Read the [README](README.md), [architecture](docs/architecture.md), and [methodology](docs/methodology.md).
2. For substantial changes, open an issue first to discuss the scope.
3. Never include credentials, private telemetry, or personal data in a commit.

## Development Setup

Use Python 3.13 and a virtual environment.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and review the settings before starting the application.

## Run and Test

Start the API and UI in separate terminals:

```bash
python scripts/run_backend.py
python scripts/run_frontend.py
```

Run the test suite:

```bash
python -m pytest
```

The API's interactive documentation is available at `http://127.0.0.1:8000/docs` while the backend is running.

## Pull Request Expectations

- Keep changes focused and explain the engineering motivation.
- Add or update tests for changed behavior.
- Run the test suite and report the result honestly.
- Update documentation, configuration examples, and methodology when behavior changes.
- Do not describe model outputs as guaranteed failures or claim metrics that have not been reproduced.
- Include screenshots for visible UI changes when practical.
