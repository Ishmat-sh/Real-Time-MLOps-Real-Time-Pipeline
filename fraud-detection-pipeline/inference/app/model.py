from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


class FraudModel:
    def __init__(self, model_path: str | Path) -> None:
        payload = joblib.load(model_path)
        self.model = payload["model"]
        self.feature_columns: list[str] = payload["feature_columns"]
        self.threshold: float = float(
            os.environ.get("FRAUD_THRESHOLD", payload.get("fraud_threshold", 0.5))
        )

    def predict_proba(self, features: dict[str, Any]) -> float:
        row = pd.DataFrame([{col: features[col] for col in self.feature_columns}])
        return float(self.model.predict_proba(row)[0, 1])

    def status(self, probability: float) -> str:
        return "flagged" if probability >= self.threshold else "approved"
