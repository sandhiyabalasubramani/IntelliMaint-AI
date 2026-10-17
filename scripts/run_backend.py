"""
IntelliMaint AI — Backend Server Launcher
"""

import sys
from pathlib import Path
import uvicorn

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings


def main():
    print("=" * 60)
    print("Starting IntelliMaint AI Backend (FastAPI)")
    print(f"Host: {settings.API_HOST} | Port: {settings.API_PORT}")
    print(f"Interactive Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("=" * 60)
    uvicorn.run(
        "backend.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
