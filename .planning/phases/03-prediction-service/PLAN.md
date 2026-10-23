# Plan 03-01: FastAPI Prediction Service & Parity Verification

## Goal
Build FastAPI prediction service exposing `/predict` (single and batch), `/health`, and `/version`, with strict Pydantic bounds checking, single-load model lifecycle, and 50-row offline parity verification.

## Requirements
- API-01: FastAPI application exposes `POST /predict` accepting single or batch raw sensor readings.
- API-02: Service exposes `GET /health` and `GET /version` endpoints.
- API-03: Strict Pydantic input validation rejects missing fields or out-of-range sensor readings with 422 errors without crashing.
- API-04: Model is loaded once into memory on application startup.
- API-05: Verification script confirms predictions on 50 sample rows match offline predictions exactly (0 drift).

## Proposed Changes
1. Create `src/schemas.py` defining Pydantic v2 schemas for raw sensor readings with field validation.
2. Create `src/app.py` implementing FastAPI endpoints with lifespan handler for model loading.
3. Create `tests/verify_parity.py` extracting 50 sample rows from `telecom_tower_failure.csv`, querying local API, and asserting exact prediction matching.

## Verification Commands
- `python tests/verify_parity.py`
