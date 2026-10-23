"""
FastAPI Tower Failure Prediction Service
Task 3 & 5 Implementation: Exposes /predict, /health, /version, and /metrics.
Loads model artifact once at startup, handles single and batch inputs, validates bounds,
and exports Prometheus metrics for live dashboard monitoring.
"""

import os
import json
import time
from contextlib import asynccontextmanager
from typing import List, Union
import numpy as np
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from schemas import (
    TowerReading,
    BatchPredictionRequest,
    PredictionResult,
    PredictionResponse,
    HealthResponse,
    VersionResponse,
)
from features import RAW_FEATURE_COLUMNS, TowerFeatureEngineer

MODEL_PATH = os.path.join("artifacts", "model_v1.joblib")
METADATA_PATH = os.path.join("artifacts", "model_metadata.json")

# Prometheus Metrics Definitions
HTTP_REQUESTS_TOTAL = Counter(
    "tower_serving_http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "tower_serving_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
PREDICTIONS_TOTAL = Counter(
    "tower_serving_predictions_total",
    "Total tower predictions made",
    ["prediction_class"],
)
FAILURE_PROBABILITY_HISTOGRAM = Histogram(
    "tower_serving_failure_probability",
    "Distribution of predicted failure probabilities",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model once into memory
    print(f"[*] Starting up Tower Prediction Service. Loading {MODEL_PATH}...")
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model artifact not found at {MODEL_PATH}. Run src/train.py first!")

    app.state.model = joblib.load(MODEL_PATH)

    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r") as f:
            app.state.metadata = json.load(f)
    else:
        app.state.metadata = {
            "model_version": "v1.0.0",
            "created_at": "unknown",
            "decision_threshold": 0.45,
        }

    print(f"[SUCCESS] Model loaded successfully: {app.state.metadata.get('model_version')}")
    yield
    # Shutdown
    print("[*] Shutting down Tower Prediction Service.")

app = FastAPI(
    title="Tower Failure Prediction Service",
    description="MLOps prediction service for mobile tower 48-hour failure prediction.",
    version="1.0.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = None
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        status_code = 500
        raise exc from None
    finally:
        duration = time.time() - start_time
        # Record metrics excluding /metrics endpoint from self-measuring loop
        if endpoint != "/metrics":
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code),
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(endpoint=endpoint).observe(duration)

    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Graceful error response for invalid types or out-of-range sensor readings."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "One or more sensor readings violate schema contract or physical plausible bounds.",
            "details": exc.errors(),
        },
    )

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint used by automated watchdog script and container probes."""
    is_loaded = hasattr(app.state, "model") and app.state.model is not None
    return HealthResponse(
        status="healthy" if is_loaded else "degraded",
        model_loaded=is_loaded,
        version=app.state.metadata.get("model_version", "unknown"),
    )

@app.get("/version", response_model=VersionResponse)
async def version():
    """Returns the versioned model artifact metadata."""
    meta = getattr(app.state, "metadata", {})
    return VersionResponse(
        model_version=meta.get("model_version", "v1.0.0"),
        created_at=meta.get("created_at", "unknown"),
        algorithm="HistGradientBoostingClassifier",
    )

@app.get("/metrics")
async def metrics():
    """Exposes Prometheus scrape metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/predict", response_model=PredictionResponse)
async def predict(payload: Union[TowerReading, BatchPredictionRequest, List[TowerReading]]):
    """
    Predict tower failure within 48 hours for a single tower or batch of towers.
    Accepts:
      - Single TowerReading object
      - BatchPredictionRequest object containing list of readings
      - Raw list of TowerReading objects
    """
    if isinstance(payload, TowerReading):
        readings = [payload]
    elif isinstance(payload, BatchPredictionRequest):
        readings = payload.readings
    elif isinstance(payload, list):
        readings = payload
    else:
        raise HTTPException(status_code=400, detail="Invalid request format")

    if not readings:
        raise HTTPException(status_code=400, detail="Empty readings list provided")

    # Direct fast NumPy array construction (bypassing pandas DataFrame allocation overhead)
    n = len(readings)
    arr = np.empty((n, 8), dtype=float)
    for i, r in enumerate(readings):
        arr[i, 0] = r.Temperature_C if r.Temperature_C is not None else np.nan
        arr[i, 1] = r.Battery_Voltage if r.Battery_Voltage is not None else np.nan
        arr[i, 2] = r.Power_Consumption_W
        arr[i, 3] = r.Signal_Strength_Percent
        arr[i, 4] = r.Fan_Speed_RPM if r.Fan_Speed_RPM is not None else np.nan
        arr[i, 5] = r.Humidity_Percent if r.Humidity_Percent is not None else np.nan
        arr[i, 6] = r.Traffic_Load
        arr[i, 7] = r.Tower_Age_Years

    model = app.state.model
    threshold = float(app.state.metadata.get("decision_threshold", 0.45))

    # Fast vectorized inference using preallocated numpy matrix
    probs = model.predict_proba(arr)[:, 1]
    preds = (probs >= threshold).astype(int)

    results: List[PredictionResult] = []
    for i, reading in enumerate(readings):
        prob = float(probs[i])
        pred = int(preds[i])
        risk = "HIGH" if pred == 1 else "LOW"

        # Record metrics
        PREDICTIONS_TOTAL.labels(prediction_class=str(pred)).inc()
        FAILURE_PROBABILITY_HISTOGRAM.observe(prob)

        results.append(
            PredictionResult(
                Tower_ID=reading.Tower_ID,
                prediction=pred,
                failure_probability=round(prob, 4),
                risk_level=risk,
            )
        )

    return PredictionResponse(
        model_version=app.state.metadata.get("model_version", "v1.0.0"),
        predictions=results,
    )
