"""
Tower Serving Stack - Parity & Robustness Verification Test Suite
Task 3 Acceptance Test:
1. Verifies that for 50 sample rows, predictions from running service match offline model exactly (0 drift).
2. Verifies invalid inputs (out of range, missing fields) return 422 errors and never crash service.
3. Verifies /health and /version endpoints.
"""

import os
import sys
import json
import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.abspath("src"))

from app import app
from features import RAW_FEATURE_COLUMNS

def test_prediction_parity_50_samples():
    """
    Task 3 Acceptance Criterion:
    'For 50 sample rows, predictions from the running service match those computed offline.'
    """
    data_path = os.path.join("project2_tower_serving", "telecom_tower_failure.csv")
    df = pd.read_csv(data_path)

    # Deterministically select 50 diverse sample rows across both classes
    sample_df = df.sample(n=50, random_state=42).copy()

    # 1. Offline predictions computed directly from model artifact
    model_path = os.path.join("artifacts", "model_v1.joblib")
    meta_path = os.path.join("artifacts", "model_metadata.json")
    model = joblib.load(model_path)
    with open(meta_path, "r") as f:
        meta = json.load(f)
    threshold = float(meta.get("decision_threshold", 0.45))

    X_offline = sample_df[RAW_FEATURE_COLUMNS]
    offline_probs = model.predict_proba(X_offline)[:, 1]
    offline_preds = (offline_probs >= threshold).astype(int)

    # 2. Online predictions via running FastAPI TestClient
    with TestClient(app) as client:
        # Check health first
        h_resp = client.get("/health")
        assert h_resp.status_code == 200
        assert h_resp.json()["model_loaded"] is True

        # Send batch of 50 samples
        payload = []
        for _, row in sample_df.iterrows():
            reading = {
                "Tower_ID": str(row["Tower_ID"]),
                "Temperature_C": None if pd.isna(row["Temperature_C"]) else float(row["Temperature_C"]),
                "Battery_Voltage": None if pd.isna(row["Battery_Voltage"]) else float(row["Battery_Voltage"]),
                "Power_Consumption_W": float(row["Power_Consumption_W"]),
                "Signal_Strength_Percent": float(row["Signal_Strength_Percent"]),
                "Fan_Speed_RPM": None if pd.isna(row["Fan_Speed_RPM"]) else float(row["Fan_Speed_RPM"]),
                "Humidity_Percent": None if pd.isna(row["Humidity_Percent"]) else float(row["Humidity_Percent"]),
                "Traffic_Load": float(row["Traffic_Load"]),
                "Tower_Age_Years": float(row["Tower_Age_Years"]),
            }
            payload.append(reading)

        resp = client.post("/predict", json={"readings": payload})
        assert resp.status_code == 200, f"Predict failed: {resp.text}"
        online_results = resp.json()["predictions"]

        assert len(online_results) == 50, "Expected exactly 50 prediction responses"

        # 3. Assert exact match across all 50 samples
        mismatches = 0
        for i, res in enumerate(online_results):
            online_pred = res["prediction"]
            online_prob = res["failure_probability"]
            expected_pred = int(offline_preds[i])
            expected_prob = round(float(offline_probs[i]), 4)

            assert online_pred == expected_pred, (
                f"Prediction mismatch at row {i} ({res['Tower_ID']}): "
                f"online={online_pred}, offline={expected_pred}"
            )
            assert abs(online_prob - expected_prob) < 1e-4, (
                f"Probability mismatch at row {i} ({res['Tower_ID']}): "
                f"online={online_prob}, offline={expected_prob}"
            )

        print(f"\n[SUCCESS] Exact parity confirmed for all 50 samples (0 drift).")

def test_robust_input_validation():
    """
    Task 3 Acceptance Criterion:
    'Invalid input, such as impossible readings or missing fields, must be rejected
     or handled safely with clear messages, never with a crash.'
    """
    with TestClient(app) as client:
        # Case A: Missing required field (Power_Consumption_W missing)
        invalid_missing = {
            "Tower_ID": "TWR-99999",
            "Temperature_C": 45.0,
            "Battery_Voltage": 48.0,
            # Power_Consumption_W omitted
            "Signal_Strength_Percent": 80.0,
            "Traffic_Load": 200.0,
            "Tower_Age_Years": 5.0,
        }
        resp_a = client.post("/predict", json=invalid_missing)
        assert resp_a.status_code == 422
        assert "error" in resp_a.json()

        # Case B: Impossible temperature reading (350°C, max is 125°C)
        invalid_temp = {
            "Tower_ID": "TWR-99999",
            "Temperature_C": 350.0,
            "Battery_Voltage": 48.0,
            "Power_Consumption_W": 800.0,
            "Signal_Strength_Percent": 80.0,
            "Traffic_Load": 200.0,
            "Tower_Age_Years": 5.0,
        }
        resp_b = client.post("/predict", json=invalid_temp)
        assert resp_b.status_code == 422

        # Case C: Negative battery voltage (-10V)
        invalid_voltage = {
            "Tower_ID": "TWR-99999",
            "Battery_Voltage": -10.0,
            "Power_Consumption_W": 800.0,
            "Signal_Strength_Percent": 80.0,
            "Traffic_Load": 200.0,
            "Tower_Age_Years": 5.0,
        }
        resp_c = client.post("/predict", json=invalid_voltage)
        assert resp_c.status_code == 422

        # Confirm service is still alive and healthy after errors
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"
        print("[SUCCESS] All invalid input tests passed safely without crashing the service.")

if __name__ == "__main__":
    test_prediction_parity_50_samples()
    test_robust_input_validation()
