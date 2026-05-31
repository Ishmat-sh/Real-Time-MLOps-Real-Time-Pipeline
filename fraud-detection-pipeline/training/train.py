#!/usr/bin/env python3
"""Train XGBoost fraud classifier and export baseline features for drift monitoring."""

from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))
MODEL_DIR = Path(os.environ.get("MODEL_DIR", "/app/output/models"))
BASELINE_DIR = DATA_DIR / "baseline"

FEATURE_COLUMNS = [
    "amount",
    "merchant_category_code",
    "hour_of_day",
    "is_weekend",
    "distance_from_home_km",
    "user_avg_spend_30d",
    "user_tx_count_30d",
    "user_failed_logins_24h",
    "user_max_spend_7d",
    "amount_to_avg_ratio",
]


def generate_training_data(n_samples: int = 50_000, fraud_rate: float = 0.04) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n_fraud = int(n_samples * fraud_rate)
    n_normal = n_samples - n_fraud

    def _block(size: int, fraudulent: bool) -> pd.DataFrame:
        amount = rng.lognormal(mean=3.5 if not fraudulent else 5.2, sigma=0.6, size=size)
        user_avg = rng.uniform(40, 350, size=size)
        return pd.DataFrame(
            {
                "amount": amount,
                "merchant_category_code": rng.integers(1000, 6000, size=size),
                "hour_of_day": rng.integers(0, 24, size=size),
                "is_weekend": rng.integers(0, 2, size=size),
                "distance_from_home_km": rng.exponential(15 if not fraudulent else 80, size=size),
                "user_avg_spend_30d": user_avg,
                "user_tx_count_30d": rng.integers(5, 150, size=size),
                "user_failed_logins_24h": rng.integers(0, 6 if fraudulent else 2, size=size),
                "user_max_spend_7d": user_avg * rng.uniform(1.2, 3.5, size=size),
                "is_fraud": int(fraudulent),
            }
        )

    normal = _block(n_normal, False)
    fraud = _block(n_fraud, True)
    df = pd.concat([normal, fraud], ignore_index=True)
    df["amount_to_avg_ratio"] = df["amount"] / df["user_avg_spend_30d"].clip(lower=1.0)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


def train() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)

    df = generate_training_data()
    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scale_pos_weight = (len(y_train) - y_train.sum()) / max(y_train.sum(), 1)
    model = xgb.XGBClassifier(
        n_estimators=120,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=float(scale_pos_weight),
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    print(f"Test ROC-AUC: {auc:.4f}")
    print(classification_report(y_test, (proba >= 0.5).astype(int)))

    model_path = MODEL_DIR / "fraud_model.pkl"
    joblib.dump(
        {
            "model": model,
            "feature_columns": FEATURE_COLUMNS,
            "fraud_threshold": float(os.environ.get("FRAUD_THRESHOLD", "0.5")),
        },
        model_path,
    )
    print(f"Saved model to {model_path}")

    baseline_path = BASELINE_DIR / "training_features.parquet"
    X.to_parquet(baseline_path, index=False)
    meta = {"feature_columns": FEATURE_COLUMNS, "n_samples": len(X), "fraud_rate": float(y.mean())}
    (BASELINE_DIR / "metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"Saved baseline features to {baseline_path}")


if __name__ == "__main__":
    train()
