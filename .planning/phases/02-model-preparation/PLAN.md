# Plan 02-01: Feature Engineering, Model Training & Input Contract

## Goal
Implement a single reusable feature module, train a tower failure prediction model on `telecom_tower_failure.csv` addressing class imbalance (~20.8%), evaluate using PR-AUC / ROC-AUC / F1, serialize a versioned model artifact, and document the input contract.

## Requirements
- MDL-01: Single reusable feature preprocessing module implemented and shared between training and serving.
- MDL-02: Binary classification model trained on `telecom_tower_failure.csv` addressing missing values and ~20.8% failure imbalance.
- MDL-03: Evaluation metric selected and justified for imbalanced data.
- MDL-04: Model saved as a versioned artifact (`artifacts/model_v1.joblib`).
- MDL-05: Raw-input schema contract documented specifying field names, data types, and plausible operational ranges.

## Proposed Changes
1. Create `src/features.py` with `TowerFeaturePipeline` (SimpleImputer, StandardScaler, domain features like temperature anomaly and power-to-traffic ratio).
2. Create `src/train.py` using scikit-learn (`HistGradientBoostingClassifier` or `RandomForestClassifier` with balanced class weights) within a serialized pipeline.
3. Save model artifact `artifacts/model_v1.joblib` and metrics summary `artifacts/model_metrics.json`.
4. Create `docs/input_contract.md` documenting schema, types, and acceptable ranges.

## Verification Commands
- `python src/train.py`
- Inspect `artifacts/model_v1.joblib` and ensure training metrics meet criteria (PR-AUC > 0.60, ROC-AUC > 0.80).
- `python -c "import joblib; m = joblib.load('artifacts/model_v1.joblib'); print(m)"`
