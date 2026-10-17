"""
IntelliMaint AI — Telemetry Dataset Loader & Synthetic Data Engine

This module provides data loading, UCI AI4I 2020 benchmark acquisition,
and a physics-based synthetic telemetry generator for predictive maintenance.
"""

from __future__ import annotations
import os
import urllib.request
import zipfile
import io
from pathlib import Path
import numpy as np
import pandas as pd


# Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "ml" / "data" / "raw"
SAMPLES_DIR = BASE_DIR / "ml" / "data" / "samples"

UCI_AI4I_URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
CSV_FILENAME = "ai4i2020.csv"

# Canonical column definitions
CANONICAL_COLUMNS = [
    "UDI",
    "Product ID",
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]

TELEMETRY_INPUT_COLUMNS = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Type",
]


def generate_synthetic_telemetry(n_samples: int = 10000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate realistic industrial telemetry following AI4I 2020 physical distributions
    and actual engineering failure laws:
    - TWF: Tool Wear Failure (tool wear reaches mechanical breakdown limit)
    - HDF: Heat Dissipation Failure (temperature delta < 8.6K and low rotational speed)
    - PWF: Power Failure (mechanical power outside 3500W - 9000W)
    - OSF: Overstrain Failure (excessive torque * tool wear product)
    - RNF: Random Failure (~0.1% baseline)
    """
    rng = np.random.default_rng(random_state)

    # 1. Product Variant (L: 50%, M: 30%, H: 20%)
    types = rng.choice(["L", "M", "H"], size=n_samples, p=[0.5, 0.3, 0.2])
    
    # Generate Product IDs
    product_ids = [f"{t}{rng.integers(10000, 99999)}" for t in types]
    udis = np.arange(1, n_samples + 1)

    # 2. Operating Temperatures (Kelvin)
    # Air temperature ~ Normal(300.0, 2.0)
    air_temp = rng.normal(loc=300.0, scale=2.0, size=n_samples)
    # Temperature difference: normally between 9.5 and 11 Kelvin
    temp_delta = rng.normal(loc=10.0, scale=1.0, size=n_samples)
    process_temp = air_temp + temp_delta

    # 3. Rotational speed (RPM) and Torque (Nm)
    # Rotational speed ~ Normal(1538, 175)
    rotational_speed = rng.normal(loc=1538.0, scale=175.0, size=n_samples)
    rotational_speed = np.clip(rotational_speed, 1100.0, 2900.0)

    # Torque is physically coupled with speed via power: Torque ~ Normal(40, 10)
    # Inverse correlation with speed plus noise
    torque_baseline = 40.0 - 0.02 * (rotational_speed - 1538.0)
    torque = rng.normal(loc=torque_baseline, scale=9.5, size=n_samples)
    torque = np.clip(torque, 3.5, 78.0)

    # 4. Tool wear (minutes): Uniform between 0 and 250 minutes
    tool_wear = rng.uniform(0.0, 250.0, size=n_samples)

    # 5. Physics-Based Failure Mode Calculation
    twf = np.zeros(n_samples, dtype=int)
    hdf = np.zeros(n_samples, dtype=int)
    pwf = np.zeros(n_samples, dtype=int)
    osf = np.zeros(n_samples, dtype=int)
    rnf = np.zeros(n_samples, dtype=int)

    # Power in Watts: P = (2 * pi * RPM / 60) * Torque
    power = (2.0 * np.pi * rotational_speed / 60.0) * torque

    # Strain product: Torque * Tool Wear
    strain = torque * tool_wear

    for i in range(n_samples):
        # TWF: Tool wear between 200 and 240 mins with increasing failure probability
        if tool_wear[i] > 200:
            if rng.random() < ((tool_wear[i] - 200) / 75.0) * 0.4:
                twf[i] = 1

        # HDF: Delta T < 8.6 K and Rotational Speed < 1380 RPM
        actual_delta = process_temp[i] - air_temp[i]
        if actual_delta < 8.6 and rotational_speed[i] < 1380.0:
            hdf[i] = 1

        # PWF: Power < 3500 W or Power > 9000 W
        if power[i] < 3500.0 or power[i] > 9000.0:
            pwf[i] = 1

        # OSF: Strain product threshold dependent on machine quality variant
        t = types[i]
        thresh = 11000.0 if t == "L" else (12000.0 if t == "M" else 13000.0)
        if strain[i] > thresh:
            osf[i] = 1

        # RNF: Random independent failure (0.1% chance)
        if rng.random() < 0.001:
            rnf[i] = 1

    # Overall machine failure (1 if any specific mode triggered)
    machine_failure = ((twf + hdf + pwf + osf + rnf) > 0).astype(int)

    df = pd.DataFrame({
        "UDI": udis,
        "Product ID": product_ids,
        "Type": types,
        "Air temperature [K]": np.round(air_temp, 2),
        "Process temperature [K]": np.round(process_temp, 2),
        "Rotational speed [rpm]": np.round(rotational_speed, 1),
        "Torque [Nm]": np.round(torque, 2),
        "Tool wear [min]": np.round(tool_wear, 0).astype(int),
        "Machine failure": machine_failure,
        "TWF": twf,
        "HDF": hdf,
        "PWF": pwf,
        "OSF": osf,
        "RNF": rnf,
    })

    return df


def download_or_generate_dataset(force_synthetic: bool = False) -> pd.DataFrame:
    """
    Load the benchmark dataset. Tries downloading the official AI4I 2020 dataset from UCI.
    If network access is unavailable, falls back gracefully to generating synthetic data.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_csv = RAW_DATA_DIR / CSV_FILENAME

    if target_csv.exists() and not force_synthetic:
        try:
            df = pd.read_csv(target_csv)
            if all(col in df.columns for col in ["Air temperature [K]", "Machine failure"]):
                return df
        except Exception:
            pass

    if not force_synthetic:
        try:
            req = urllib.request.Request(
                UCI_AI4I_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                zip_data = resp.read()
                with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                    for filename in z.namelist():
                        if filename.endswith(".csv"):
                            content = z.read(filename)
                            with open(target_csv, "wb") as f:
                                f.write(content)
                            df = pd.read_csv(target_csv)
                            return df
        except Exception:
            # Fallback to high-fidelity synthetic data
            pass

    df = generate_synthetic_telemetry(n_samples=10000, random_state=42)
    df.to_csv(target_csv, index=False)
    return df


def create_sample_csv_templates() -> tuple[Path, Path]:
    """
    Creates two demonstration CSV files:
    1. sample_telemetry_template.csv: Empty template with headers and 3 clean example rows.
    2. sample_telemetry_demo.csv: 60 realistic rows showing diverse operations (normal, high wear, thermal spike).
    """
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    template_path = SAMPLES_DIR / "sample_telemetry_template.csv"
    demo_path = SAMPLES_DIR / "sample_telemetry_demo.csv"

    # Template (minimal example for user to fill)
    template_df = pd.DataFrame([
        {
            "Machine Reference": "CNC-MILL-01",
            "Type": "M",
            "Air temperature [K]": 298.5,
            "Process temperature [K]": 308.7,
            "Rotational speed [rpm]": 1500.0,
            "Torque [Nm]": 42.0,
            "Tool wear [min]": 45,
        },
        {
            "Machine Reference": "CNC-MILL-02",
            "Type": "L",
            "Air temperature [K]": 300.2,
            "Process temperature [K]": 310.5,
            "Rotational speed [rpm]": 1420.0,
            "Torque [Nm]": 48.5,
            "Tool wear [min]": 120,
        },
        {
            "Machine Reference": "CNC-MILL-03",
            "Type": "H",
            "Air temperature [K]": 302.1,
            "Process temperature [K]": 311.2,
            "Rotational speed [rpm]": 1610.0,
            "Torque [Nm]": 38.2,
            "Tool wear [min]": 15,
        },
    ])
    template_df.to_csv(template_path, index=False)

    # Rich Demo telemetry dataset with 60 labeled rows for UI demonstrations
    demo_df = generate_synthetic_telemetry(n_samples=60, random_state=123)
    # Add Machine Reference for upload correlation
    demo_df["Machine Reference"] = [f"CNC-MILL-{(i % 6) + 1:02d}" for i in range(len(demo_df))]
    
    # Reorder columns to place Machine Reference first
    cols = ["Machine Reference"] + [c for c in demo_df.columns if c != "Machine Reference"]
    demo_df = demo_df[cols]
    demo_df.to_csv(demo_path, index=False)

    return template_path, demo_path


if __name__ == "__main__":
    print("Initializing benchmark dataset and demonstration CSV files...")
    df = download_or_generate_dataset()
    print(f"Dataset ready. Total rows: {len(df)}, Failure prevalence: {df['Machine failure'].mean():.2%}")
    tmpl, demo = create_sample_csv_templates()
    print(f"Template created: {tmpl}")
    print(f"Demo CSV created: {demo}")
