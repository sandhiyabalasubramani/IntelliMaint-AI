"""
IntelliMaint AI — Real-time Failure Risk Predictor & Explainability Engine

Provides real-time model inference, calibrated risk scoring,
physics-based telemetry diagnostics, and feature contribution explanations.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "ml" / "models" / "best_model.joblib"
METADATA_PATH = BASE_DIR / "ml" / "models" / "model_metadata.json"


class ModelNotTrainedError(Exception):
    """Raised when an inference is requested but the model artifact is missing."""
    pass


class FailureRiskPredictor:
    """
    Inference and explainability engine for machine failure risk.
    Computes calibrated probability, risk tier, contributing telemetry factors,
    and recommended inspection actions.
    """

    def __init__(self, model_path: Path = MODEL_PATH, metadata_path: Path = METADATA_PATH):
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self._model = None
        self._metadata = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads serialized model artifact and metadata if present."""
        if self.model_path.exists():
            try:
                self._model = joblib.load(self.model_path)
            except Exception as e:
                self._model = None

        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except Exception:
                self._metadata = None

    @property
    def is_ready(self) -> bool:
        """Returns True if the ML model is loaded and ready for predictions."""
        return self._model is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns model training metadata or fallback default."""
        if self._metadata:
            return self._metadata
        return {
            "model_version": "1.0.0 (unloaded)",
            "champion_algorithm": "Model not yet trained",
            "test_metrics": {},
        }

    def _classify_risk_tier(self, probability: float) -> str:
        """
        Maps probability to calibrated industrial risk categories:
        - Low Risk: P < 0.25 (Normal operating envelope)
        - Medium Risk: 0.25 <= P < 0.65 (Early degradation / advisory)
        - High Risk: P >= 0.65 (Critical risk threshold / urgent inspection)
        """
        if probability < 0.25:
            return "Low"
        elif probability < 0.65:
            return "Medium"
        else:
            return "High"

    def _derive_physical_indicators(
        self,
        air_temp: float,
        process_temp: float,
        rotational_speed: float,
        torque: float,
        tool_wear: float,
    ) -> Dict[str, float]:
        """Calculates derived engineering parameters with proper SI units."""
        temp_diff = float(process_temp - air_temp)
        # Power (Watts): P = (2 * pi * RPM / 60) * Torque
        mechanical_power = float((2.0 * np.pi * rotational_speed / 60.0) * torque)
        strain_product = float(torque * tool_wear)

        return {
            "temp_diff_kelvin": round(temp_diff, 2),
            "mechanical_power_watts": round(mechanical_power, 2),
            "strain_product_nm_min": round(strain_product, 2),
        }

    def _generate_explainability(
        self,
        telemetry: Dict[str, Any],
        indicators: Dict[str, float],
        probability: float,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Generates explainable factors and recommended maintenance actions
        based on feature deviations from safe operating envelopes.
        """
        factors: List[Dict[str, Any]] = []
        actions: List[str] = []

        air_temp = float(telemetry.get("Air temperature [K]", 300.0))
        proc_temp = float(telemetry.get("Process temperature [K]", 310.0))
        speed = float(telemetry.get("Rotational speed [rpm]", 1500.0))
        torque = float(telemetry.get("Torque [Nm]", 40.0))
        tool_wear = float(telemetry.get("Tool wear [min]", 50.0))

        delta_t = indicators["temp_diff_kelvin"]
        power = indicators["mechanical_power_watts"]
        strain = indicators["strain_product_nm_min"]

        # 1. Heat Dissipation Analysis (HDF mode check)
        if delta_t < 8.6 and speed < 1380.0:
            factors.append({
                "factor": "Thermal Dissipation Deficit",
                "severity": "High",
                "value": f"{delta_t:.1f} K (threshold < 8.6 K at {speed:.0f} RPM)",
                "impact": "Insufficient heat convection between cutting zone and ambient environment.",
            })
            actions.append("Inspect coolant pump pressure, flow valves, and heat exchanger fins.")
        elif delta_t < 9.0:
            factors.append({
                "factor": "Marginal Heat Dissipation",
                "severity": "Medium",
                "value": f"{delta_t:.1f} K",
                "impact": "Temperature differential is near lower operational limit.",
            })

        # 2. Tool Wear Analysis (TWF mode check)
        if tool_wear >= 200.0:
            factors.append({
                "factor": "Critical Cutting Edge Wear",
                "severity": "High",
                "value": f"{tool_wear:.0f} min (critical threshold >= 200 min)",
                "impact": "High risk of tool flank fracture and workpiece surface damage.",
            })
            actions.append("Schedule immediate tool insert replacement before next production cycle.")
        elif tool_wear >= 160.0:
            factors.append({
                "factor": "Advanced Tool Wear",
                "severity": "Medium",
                "value": f"{tool_wear:.0f} min",
                "impact": "Approaching scheduled wear tolerance limit.",
            })
            actions.append("Inspect cutting insert for micro-chipping; queue replacement tooling.")

        # 3. Mechanical Power Analysis (PWF mode check)
        if power < 3500.0 or power > 9000.0:
            factors.append({
                "factor": "Abnormal Motor Power Consumption",
                "severity": "High",
                "value": f"{power:.0f} W (nominal envelope: 3,500 W - 9,000 W)",
                "impact": "Motor drive operating outside design power window (stall or over-speed risk).",
            })
            actions.append("Calibrate variable frequency drive (VFD) and inspect spindle bearings for mechanical binding.")

        # 4. Mechanical Strain Analysis (OSF mode check)
        if strain > 11000.0:
            factors.append({
                "factor": "Excessive Mechanical Strain",
                "severity": "High",
                "value": f"{strain:.0f} Nm·min (threshold > 11,000)",
                "impact": "High torque combined with accumulated tool wear creates extreme spindle load.",
            })
            actions.append("Reduce feed rate and Spindle RPM override to alleviate cutting torque.")

        # Default routine recommendations if normal
        if not actions:
            if probability >= 0.25:
                actions.append("Perform routine acoustic vibration scan and verify lubrication levels.")
            else:
                actions.append("Machine telemetry within nominal envelope. Continue standard maintenance schedule.")

        return factors, actions

    def predict_single(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs failure risk assessment for a single telemetry record.
        """
        if not self.is_ready:
            raise ModelNotTrainedError(
                "Model artifact not found. Please train the model via scripts/train_model.py or ml/src/train.py."
            )

        # Standardize input dictionary
        df_in = pd.DataFrame([telemetry])

        # Ensure required columns exist
        required_cols = [
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]",
        ]
        for col in required_cols:
            if col not in df_in.columns:
                raise ValueError(f"Missing required telemetry parameter: '{col}'")

        if "Type" not in df_in.columns:
            df_in["Type"] = "M"

        # Predict probability
        try:
            prob = float(self._model.predict_proba(df_in)[:, 1][0])
            pred_class = int(prob >= 0.5)
        except Exception as e:
            # Fallback if model doesn't support predict_proba
            pred_class = int(self._model.predict(df_in)[0])
            prob = 0.85 if pred_class == 1 else 0.05

        risk_tier = self._classify_risk_tier(prob)

        # Calculate physical indicators
        indicators = self._derive_physical_indicators(
            air_temp=float(telemetry["Air temperature [K]"]),
            process_temp=float(telemetry["Process temperature [K]"]),
            rotational_speed=float(telemetry["Rotational speed [rpm]"]),
            torque=float(telemetry["Torque [Nm]"]),
            tool_wear=float(telemetry["Tool wear [min]"]),
        )

        factors, actions = self._generate_explainability(telemetry, indicators, prob)

        meta = self.get_metadata()

        return {
            "failure_probability": round(prob, 4),
            "predicted_failure": pred_class,
            "risk_tier": risk_tier,
            "physical_indicators": indicators,
            "contributing_factors": factors,
            "suggested_actions": actions,
            "model_version": meta.get("model_version", "1.0.0"),
            "model_algorithm": meta.get("champion_algorithm", "Ensemble"),
            "disclaimer": (
                "Educational and portfolio demonstration. Risk categories are operational "
                "decision-support indicators, not certified industrial safety thresholds."
            ),
        }

    def predict_batch(self, df_telemetry: pd.DataFrame) -> pd.DataFrame:
        """
        Vectorized batch assessment for uploaded telemetry datasets.
        Returns the original DataFrame enriched with predictions, probabilities, and risk tiers.
        """
        if not self.is_ready:
            raise ModelNotTrainedError(
                "Model artifact not found. Please train the model before batch analysis."
            )

        df = df_telemetry.copy()
        if "Type" not in df.columns:
            df["Type"] = "M"

        probs = self._model.predict_proba(df)[:, 1]
        df["failure_probability"] = np.round(probs, 4)
        df["predicted_failure"] = (probs >= 0.5).astype(int)
        df["risk_tier"] = [self._classify_risk_tier(p) for p in probs]

        # Add physical indicators
        speed = df["Rotational speed [rpm]"].values
        torque = df["Torque [Nm]"].values
        air_t = df["Air temperature [K]"].values
        proc_t = df["Process temperature [K]"].values
        wear = df["Tool wear [min]"].values

        df["temp_diff_kelvin"] = np.round(proc_t - air_t, 2)
        df["mechanical_power_watts"] = np.round((2.0 * np.pi * speed / 60.0) * torque, 2)
        df["strain_product"] = np.round(torque * wear, 2)

        return df
