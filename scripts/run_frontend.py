"""
IntelliMaint AI — Streamlit Frontend Launcher
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_APP = BASE_DIR / "frontend" / "app.py"


def main():
    print("=" * 60)
    print("Starting IntelliMaint AI Frontend (Streamlit)")
    print(f"Target App: {FRONTEND_APP}")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(FRONTEND_APP),
        "--server.port=8501",
        "--server.address=127.0.0.1",
        "--browser.gatherUsageStats=false",
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
