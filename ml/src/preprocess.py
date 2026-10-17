"""
IntelliMaint AI — Telemetry Feature Engineering & Preprocessing Pipeline
"""

from __future__ import annotations
from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer


# Non-feature identifier and target columns to exclude from training features
EXCLUDE_COLUMNS = [
    "UDI",
    "Product ID",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
    "Machine Reference",
    "timestamp",
]

RAW_NUMERIC_FEATURES = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

RAW_CATEGORICAL_FEATURES = ["Type"]

ENGINEERED_FEATURE_NAMES = [
    "temp_diff",
    "power_watts",
    "strain_product",
    "temp_ratio",
    "torque_speed_ratio",
]


class EngineeringFeaturesTransformer(BaseEstimator, TransformerMixin):
    """
    Computes physics-grounded electrical and mechanical features from telemetry:
    1. Temperature difference: Process Temp - Air Temp (Kelvin) [Key indicator for Heat Dissipation Failure]
    2. Mechanical Power (W): P = (2 * pi * RPM / 60) * Torque [Indicator for Power Failure]
    3. Strain product: Torque * Tool Wear [Key indicator for Overstrain Failure]
    4. Temperature ratio: Process Temp / Air Temp
    5. Torque to speed ratio: Torque / (RPM + 1e-5)
    """

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        
        # Ensure raw numeric features exist
        air_temp = df["Air temperature [K]"].values.astype(float)
        proc_temp = df["Process temperature [K]"].values.astype(float)
        speed = df["Rotational speed [rpm]"].values.astype(float)
        torque = df["Torque [Nm]"].values.astype(float)
        wear = df["Tool wear [min]"].values.astype(float)

        # 1. Delta T (Heat dissipation)
        df["temp_diff"] = proc_temp - air_temp
        
        # 2. Mechanical Power (Watts): P = (2 * pi * RPM / 60) * Torque
        df["power_watts"] = (2.0 * np.pi * speed / 60.0) * torque
        
        # 3. Strain Product: Torque * Tool Wear
        df["strain_product"] = torque * wear

        # 4. Thermal Ratio
        df["temp_ratio"] = proc_temp / np.maximum(air_temp, 1e-3)

        # 5. Torque to Speed Ratio
        df["torque_speed_ratio"] = torque / np.maximum(speed, 1e-3)

        return df


def get_feature_columns() -> Tuple[List[str], List[str]]:
    """Return lists of numeric (including engineered) and categorical feature names."""
    all_numeric = RAW_NUMERIC_FEATURES + ENGINEERED_FEATURE_NAMES
    all_categorical = RAW_CATEGORICAL_FEATURES
    return all_numeric, all_categorical


def build_preprocessing_pipeline() -> Pipeline:
    """
    Constructs a robust scikit-learn Pipeline with:
    - Feature engineering
    - Missing value imputation
    - Continuous feature standard scaling
    - Categorical one-hot encoding
    """
    numeric_features, categorical_features = get_feature_columns()

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )

    full_pipeline = Pipeline(
        steps=[
            ("engineer", EngineeringFeaturesTransformer()),
            ("preprocessor", preprocessor),
        ]
    )

    return full_pipeline
