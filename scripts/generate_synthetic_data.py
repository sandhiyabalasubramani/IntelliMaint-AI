"""
IntelliMaint AI — Synthetic Data & Sample CSV Generation Script
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from ml.src.dataset import download_or_generate_dataset, create_sample_csv_templates


def main():
    print("=" * 60)
    print("IntelliMaint AI — Telemetry & Dataset Setup")
    print("=" * 60)

    print("\n[1/2] Fetching / generating benchmark AI4I 2020 dataset...")
    df = download_or_generate_dataset()
    print(f" -> Success: {len(df):,} records loaded.")
    print(f" -> Failure incidence: {df['Machine failure'].sum():,} ({df['Machine failure'].mean():.2%})")
    print(f" -> Machine Quality Distribution:\n{df['Type'].value_counts(normalize=True).apply(lambda x: f'{x:.1%}')}")

    print("\n[2/2] Generating downloadable template and demonstration CSVs...")
    tmpl, demo = create_sample_csv_templates()
    print(f" -> Template CSV: {tmpl}")
    print(f" -> Demonstration CSV: {demo}")
    print("\nDone! All sample and training datasets are ready.\n")


if __name__ == "__main__":
    main()
