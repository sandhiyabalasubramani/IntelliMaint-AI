"""
IntelliMaint AI — Machine Learning Model Training & Benchmark Pipeline

Trains, compares, and evaluates multiple candidate models for industrial failure risk:
- Logistic Regression (balanced weights baseline)
- Random Forest Classifier (balanced ensemble)
- Gradient Boosting Classifier (boosted trees)

Selects the champion model based on F1-score & PR-AUC, then persists model artifacts
and comprehensive metadata to ml/models/.
"""

from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.src.dataset import download_or_generate_dataset
from ml.src.preprocess import (
    build_preprocessing_pipeline,
    get_feature_columns,
    EXCLUDE_COLUMNS,
)
from ml.src.evaluate import evaluate_classifier

MODEL_DIR = BASE_DIR / "ml" / "models"
MODEL_PATH = MODEL_DIR / "best_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"


def prepare_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract features and target label from raw dataframe."""
    target_col = "Machine failure"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    # Drop non-feature and leakage columns
    feature_cols = [c for c in df.columns if c not in EXCLUDE_COLUMNS]
    X = df[feature_cols].copy()
    y = df[target_col].astype(int).copy()
    return X, y


def train_and_compare_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    dataset_name: str = "UCI AI4I 2020 / Synthetic",
) -> Tuple[Pipeline, Dict[str, Any], Dict[str, Any]]:
    """
    Trains multiple models, evaluates each on the held-out test split,
    and returns the best pipeline along with comparative benchmark metrics.
    """
    preprocessor = build_preprocessing_pipeline()

    # Define candidate classifiers
    candidates = {
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            min_samples_split=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
        ),
        "Logistic Regression": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        ),
    }

    benchmark_results: Dict[str, Any] = {}
    best_name: str = ""
    best_f1: float = -1.0
    best_pipeline: Pipeline | None = None
    best_metrics: Dict[str, Any] = {}

    print(f"\nTraining set size: {len(X_train)} | Test set size: {len(X_test)}")
    print(f"Training failure prevalence: {y_train.mean():.2%} | Test failure prevalence: {y_test.mean():.2%}\n")

    for name, clf in candidates.items():
        print(f"--> Training {name}...")
        pipeline = Pipeline(
            steps=[
                ("prep", preprocessor),
                ("classifier", clf),
            ]
        )

        pipeline.fit(X_train, y_train)

        # Predictions on held-out test set
        y_pred = pipeline.predict(X_test)
        y_prob = (
            pipeline.predict_proba(X_test)[:, 1]
            if hasattr(pipeline, "predict_proba")
            else None
        )

        eval_res = evaluate_classifier(y_test.values, y_pred, y_prob)
        benchmark_results[name] = eval_res

        f1 = eval_res["f1_score"]
        pr_auc = eval_res.get("pr_auc") or 0.0
        roc_auc = eval_res.get("roc_auc") or 0.0

        print(
            f"    Precision: {eval_res['precision']:.3f} | Recall: {eval_res['recall']:.3f} | "
            f"F1: {f1:.3f} | ROC-AUC: {roc_auc:.3f} | PR-AUC: {pr_auc:.3f}"
        )

        # Select best model using F1 score (and PR-AUC as tie-breaker)
        if f1 > best_f1:
            best_f1 = f1
            best_name = name
            best_pipeline = pipeline
            best_metrics = eval_res

    print(f"\n[WINNER] Selected Champion Model: {best_name} (F1 Score: {best_f1:.4f})")

    # Extract feature importances if available
    feature_importances: Dict[str, float] = {}
    try:
        classifier_step = best_pipeline.named_steps["classifier"]
        prep_step = best_pipeline.named_steps["prep"]
        
        # Get feature names from ColumnTransformer
        col_transformer = prep_step.named_steps["preprocessor"]
        numeric_cols, cat_cols = get_feature_columns()
        
        # Get one-hot encoded categories
        cat_encoder = col_transformer.named_transformers_["cat"].named_steps["encoder"]
        cat_encoded_names = list(cat_encoder.get_feature_names_out(cat_cols))
        transformed_feature_names = numeric_cols + cat_encoded_names

        if hasattr(classifier_step, "feature_importances_"):
            importances = classifier_step.feature_importances_
            for fname, imp in zip(transformed_feature_names, importances):
                feature_importances[fname] = float(imp)
        elif hasattr(classifier_step, "coef_"):
            coefs = np.abs(classifier_step.coef_[0])
            for fname, coef in zip(transformed_feature_names, coefs):
                feature_importances[fname] = float(coef)
    except Exception as e:
        print(f"Notice: Could not extract feature importances: {e}")

    # Build metadata
    metadata = {
        "model_version": "1.0.0",
        "champion_algorithm": best_name,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_source": dataset_name,
        "total_records": len(X_train) + len(X_test),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_failure_count": int(y_test.sum()),
        "test_metrics": best_metrics,
        "benchmark_comparison": {
            name: {
                "precision": res["precision"],
                "recall": res["recall"],
                "f1_score": res["f1_score"],
                "roc_auc": res.get("roc_auc"),
                "pr_auc": res.get("pr_auc"),
                "accuracy": res["accuracy"],
            }
            for name, res in benchmark_results.items()
        },
        "feature_importances": dict(
            sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
        ),
        "risk_thresholds": {
            "low": "< 0.25",
            "medium": "0.25 - 0.65",
            "high": ">= 0.65",
        },
        "operational_disclaimer": (
            "Educational and portfolio demonstration model. Risk predictions represent "
            "statistical estimations and must not supersede certified industrial safety systems."
        ),
    }

    return best_pipeline, metadata, benchmark_results


def train_model() -> Tuple[Pipeline, Dict[str, Any]]:
    """Loads dataset, trains models, evaluates, and persists the champion model."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("IntelliMaint AI — Machine Learning Pipeline Training")
    print("=" * 60)

    print("\n[Step 1/3] Loading dataset...")
    df = download_or_generate_dataset()
    print(f"Dataset ready with {len(df):,} records.")

    print("\n[Step 2/3] Extracting features and running stratified train-test split (80/20)...")
    X, y = prepare_data(df)
    
    # Stratified train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("\n[Step 3/3] Training and comparing candidate algorithms...")
    best_pipeline, metadata, _ = train_and_compare_models(
        X_train, X_test, y_train, y_test, dataset_name="UCI AI4I 2020 / Synthetic Telemetry"
    )

    # Persist model artifact
    print(f"\nPersisting champion model artifact to: {MODEL_PATH}")
    joblib.dump(best_pipeline, MODEL_PATH)

    # Persist metadata JSON
    print(f"Persisting model metadata to: {METADATA_PATH}")
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\nTraining completed successfully! Artifacts are ready for inference.")
    return best_pipeline, metadata


if __name__ == "__main__":
    train_model()
