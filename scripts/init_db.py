"""
IntelliMaint AI — Database Initialization Script
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import init_db, engine
from backend.app.config import settings


def main():
    print("=" * 60)
    print("IntelliMaint AI — Database Table Initialization")
    print("=" * 60)
    print(f"Target Database URL: {settings.DATABASE_URL}")

    try:
        init_db()
        print("Success: All database tables created / verified.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
