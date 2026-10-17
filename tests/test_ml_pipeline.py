"""
IntelliMaint AI — Machine Learning Pipeline & Inference Tests
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from ml.src.dataset import generate_synthetic_telemetry
from ml.src.preprocess import (
    EngineeringFeaturesTransformer,
    build_preprocessing_pipeline,
)
from ml.src.evaluate import evaluate_classifier
from ml.src.train import train_and_compare_models, prepare_data
from ml.src.predictor import FailureRiskPredictor, ModelNotTrainedError


def test_engineering_features_transformer():
    """Test 11: Verify physics feature engineering correctly derives physical quantities."""
    df_raw = pd.DataFrame({
        "Air temperature [K]": [300.0],
        "Process temperature [K]": [310.0],
        "Rotational speed [rpm]": [1500.0],
        "Torque [Nm]": [40.0],
        "Tool wear [min]": [50.0],
        "Type": ["M"],
    })

    transformer = EngineeringFeaturesTransformer()
    df_feat = transformer.transform(df_raw)

    assert "temp_diff" in df_feat.columns
    assert "power_watts" in df_feat.columns
    assert "strain_product" in df_feat.columns

    # Verify formulas
    # 1. Delta T = 310 - 300 = 10.0
    assert df_feat["temp_diff"].iloc[0] == pytest.approx(10.0)
    # 2. Power = (2 * pi * 1500 / 60) * 40 = 50 * pi * 40 = 2000 * pi ~ 6283.185 W
    expected_power = (2.0 * np.pi * 1500.0 / 60.0) * 40.0
    assert df_feat["power_watts"].iloc[0] == pytest.approx(expected_power, rel=1e-3)
    # 3. Strain = 40 * 50 = 2000
    assert df_feat["strain_product"].iloc[0] == pytest.approx(2000.0)


def test_model_training_and_evaluation_fixture():
    """Test 12 & 13: Train and compare models on a synthetic fixture with class imbalance."""
    df_fixture = generate_synthetic_telemetry(n_samples=300, random_state=42)
    X, y = prepare_data(df_fixture)

    # Train/test split
    split_idx = 240
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    pipeline, metadata, benchmark = train_and_compare_models(
        X_train, X_test, y_train, y_test, dataset_name="Test Fixture"
    )

    assert pipeline is not None
    assert "champion_algorithm" in metadata
    assert "test_metrics" in metadata
    assert "f1_score" in metadata["test_metrics"]
    assert "Random Forest" in benchmark
    assert "Gradient Boosting" in benchmark


def test_prediction_output_bounds_and_risk_tiers():
    """Test 14: Predictor probabilities are strictly bounded [0.0, 1.0] and risk tiers map accurately."""
    predictor = FailureRiskPredictor()
    if not predictor.is_ready:
        pytest.skip("Model artifact not present in environment.")

    # 1. Normal telemetry
    normal_telemetry = {
        "Air temperature [K]": 298.5,
        "Process temperature [K]": 308.7,
        "Rotational speed [rpm]": 1520.0,
        "Torque [Nm]": 38.0,
        "Tool wear [min]": 30.0,
        "Type": "M",
    }
    res_normal = predictor.predict_single(normal_telemetry)
    assert 0.0 <= res_normal["failure_probability"] <= 1.0
    assert res_normal["risk_tier"] in ["Low", "Medium", "High"]

    # 2. Critical telemetry (extreme tool wear and torque)
    critical_telemetry = {
        "Air temperature [K]": 302.0,
        "Process temperature [K]": 308.0,  # Delta T is 6.0 (thermal deficit)
        "Rotational speed [rpm]": 1300.0,
        "Torque [Nm]": 65.0,
        "Tool wear [min]": 230.0,
        "Type": "L",
    }
    res_critical = predictor.predict_single(critical_telemetry)
    assert 0.0 <= res_critical["failure_probability"] <= 1.0
    assert res_critical["risk_tier"] in ["Medium", "High"]
    assert len(res_critical["contributing_factors"]) > 0


def test_missing_model_behavior(tmp_path):
    """Test 15: Missing model artifact raises clean ModelNotTrainedError upon inference."""
    non_existent_model = tmp_path / "non_existent_model.joblib"
    predictor = FailureRiskPredictor(model_path=non_existent_model)
    assert predictor.is_ready is False

    with pytest.raises(ModelNotTrainedError):
        predictor.predict_single({"Air temperature [K]": 300.0})
