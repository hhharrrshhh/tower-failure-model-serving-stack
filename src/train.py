"""
Tower Serving Stack - Model Training & Evaluation Pipeline
Task 2 Implementation: Trains failure prediction model on telecom_tower_failure.csv,
evaluates using metrics justified for imbalanced data, and saves versioned artifacts.
"""

import os
import json
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
)

from features import RAW_FEATURE_COLUMNS, TowerFeatureEngineer

DATA_PATH = os.path.join("project2_tower_serving", "telecom_tower_failure.csv")
ARTIFACTS_DIR = "artifacts"
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "model_v1.joblib")
METRICS_PATH = os.path.join(ARTIFACTS_DIR, "model_metadata.json")

def train_and_evaluate():
    print(f"[*] Loading training dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    X = df[RAW_FEATURE_COLUMNS].copy()
    y = df["Failure_Within_48Hrs"].copy()

    total_samples = len(df)
    positive_samples = int(y.sum())
    failure_rate = float(positive_samples / total_samples)
    print(f"[*] Total rows: {total_samples}, Positive failures: {positive_samples} ({failure_rate:.1%})")

    # Stratified 80/20 train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("[*] Assembling end-to-end Pipeline (TowerFeatureEngineer + HistGradientBoostingClassifier)...")
    pipeline = Pipeline(
        steps=[
            ("feature_engineer", TowerFeatureEngineer()),
            (
                "classifier",
                HistGradientBoostingClassifier(
                    class_weight="balanced",
                    random_state=42,
                    max_iter=150,
                    min_samples_leaf=20,
                    learning_rate=0.08,
                ),
            ),
        ]
    )

    print("[*] Training model pipeline...")
    pipeline.fit(X_train, y_train)

    print("[*] Evaluating on held-out test split (300 samples)...")
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    # Threshold selection calibrated for early failure intervention
    decision_threshold = 0.45
    y_pred = (y_prob >= decision_threshold).astype(int)

    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    f1 = float(f1_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred))
    recall = float(recall_score(y_test, y_pred))
    cm = confusion_matrix(y_test, y_pred).tolist()

    print(f"\n================ EVALUATION METRICS ================")
    print(f"ROC-AUC:               {roc_auc:.4f}")
    print(f"PR-AUC (Avg Precision): {pr_auc:.4f}  (Random baseline: {failure_rate:.4f})")
    print(f"Decision Threshold:    {decision_threshold}")
    print(f"Precision (Failure):   {precision:.4f}")
    print(f"Recall (Failure):      {recall:.4f}")
    print(f"F1-Score (Failure):    {f1:.4f}")
    print(f"Confusion Matrix [TN, FP / FN, TP]: {cm}")
    print("====================================================\n")

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    metadata = {
        "model_version": "v1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "failure_rate": failure_rate,
        "features": RAW_FEATURE_COLUMNS,
        "decision_threshold": decision_threshold,
        "metrics": {
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "f1_score": f1,
            "precision": precision,
            "recall": recall,
            "confusion_matrix": cm,
        },
        "evaluation_justification": (
            "Because only ~20.8% of towers fail within 48 hours (imbalanced dataset), "
            "standard accuracy is misleading. Precision-Recall AUC (PR-AUC) and F1-score with balanced "
            "loss weighting are prioritized to penalize missed tower failures (False Negatives) while "
            "maintaining actionable alerting precision."
        ),
    }

    print(f"[*] Saving serialized model pipeline to {MODEL_PATH}...")
    joblib.dump(pipeline, MODEL_PATH)

    print(f"[*] Saving model metadata to {METRICS_PATH}...")
    with open(METRICS_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print("[SUCCESS] Model preparation and serialization completed successfully.")
    return pipeline, metadata

if __name__ == "__main__":
    train_and_evaluate()
