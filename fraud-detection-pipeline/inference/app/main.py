from __future__ import annotations

import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.feast_client import FeastFeatureClient
from app.metrics import FRAUD_FLAGGED_TOTAL, PREDICTION_LATENCY, PREDICTIONS_TOTAL
from app.model import FraudModel
from app.schemas import PredictionResponse, Transaction

DRIFT_SAMPLE_DIR = Path(os.environ.get("DRIFT_SAMPLE_DIR", "/app/drift_samples"))
MODEL: FraudModel | None = None
FEAST: FeastFeatureClient | None = None


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global MODEL, FEAST
    model_path = os.environ.get("MODEL_PATH", "/app/models/fraud_model.pkl")
    if not Path(model_path).exists():
        raise RuntimeError(f"Model not found at {model_path}. Run training first.")
    MODEL = FraudModel(model_path)
    FEAST = FeastFeatureClient()
    DRIFT_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Fraud Detection Inference API",
    description="Real-time credit card fraud scoring with Feast feature enrichment",
    version="1.0.0",
    lifespan=lifespan,
)


def build_feature_vector(tx: Transaction, historical: dict) -> dict:
    amount = tx.amount
    user_avg = float(historical["user_avg_spend_30d"])
    return {
        "amount": amount,
        "merchant_category_code": tx.merchant_category_code,
        "hour_of_day": tx.hour_of_day,
        "is_weekend": tx.is_weekend,
        "distance_from_home_km": tx.distance_from_home_km,
        "user_avg_spend_30d": user_avg,
        "user_tx_count_30d": int(historical["user_tx_count_30d"]),
        "user_failed_logins_24h": int(historical["user_failed_logins_24h"]),
        "user_max_spend_7d": float(historical["user_max_spend_7d"]),
        "amount_to_avg_ratio": amount / max(user_avg, 1.0),
    }


def append_drift_sample(features: dict, probability: float, status: str) -> None:
    sample = {**features, "fraud_probability": probability, "status": status}
    path = DRIFT_SAMPLE_DIR / "production_samples.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model_loaded": str(MODEL is not None)}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: Transaction) -> PredictionResponse:
    if MODEL is None or FEAST is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    start = time.perf_counter()
    historical = FEAST.get_user_features(transaction.user_id)
    features = build_feature_vector(transaction, historical)
    probability = MODEL.predict_proba(features)
    status = MODEL.status(probability)
    latency_ms = (time.perf_counter() - start) * 1000

    PREDICTIONS_TOTAL.labels(status=status).inc()
    if status == "flagged":
        FRAUD_FLAGGED_TOTAL.inc()
    PREDICTION_LATENCY.observe(latency_ms / 1000)

    append_drift_sample(features, probability, status)

    return PredictionResponse(
        transaction_id=transaction.transaction_id,
        status=status,
        fraud_probability=round(probability, 4),
        latency_ms=round(latency_ms, 2),
    )
