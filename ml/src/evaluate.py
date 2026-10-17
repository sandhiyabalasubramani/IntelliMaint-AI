"""
IntelliMaint AI — Machine Learning Evaluation Engine

Computes precision, recall, F1-score, ROC-AUC, Average Precision (PR-AUC),
and confusion matrix metrics for imbalanced industrial predictive maintenance data.
"""

from __future__ import annotations
from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
    accuracy_score,
)


def evaluate_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray | None = None,
) -> Dict[str, Any]:
    """
    Evaluates predictions against ground truth labels with industrial safety focus.
    In predictive maintenance, Recall (detecting actual failures) and Precision
    (avoiding false alarms) are strictly evaluated via F1 and PR-AUC.
    """
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = (
        int(cm[0, 0]),
        int(cm[0, 1]),
        int(cm[1, 0]),
        int(cm[1, 1]),
    ) if cm.shape == (2, 2) else (int(cm[0, 0]), 0, 0, 0)

    total = len(y_true)
    failure_prevalence = float(np.mean(y_true))

    metrics: Dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "true_positives": tp,
        "total_samples": total,
        "failure_prevalence": failure_prevalence,
        "confusion_matrix": [[tn, fp], [fn, tp]],
    }

    if y_prob is not None and len(np.unique(y_true)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except Exception:
            metrics["roc_auc"] = None

        try:
            metrics["pr_auc"] = float(average_precision_score(y_true, y_prob))
        except Exception:
            metrics["pr_auc"] = None
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None

    metrics["classification_report"] = classification_report(
        y_true, y_pred, output_dict=True, zero_division=0
    )

    return metrics
