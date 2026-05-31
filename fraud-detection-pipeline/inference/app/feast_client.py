from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from feast import FeatureStore

from app.metrics import FEATURE_FETCH_LATENCY

FEATURE_REFS = [
    "user_stats:user_avg_spend_30d",
    "user_stats:user_tx_count_30d",
    "user_stats:user_failed_logins_24h",
    "user_stats:user_max_spend_7d",
]

DEFAULT_FEATURES = {
    "user_avg_spend_30d": 100.0,
    "user_tx_count_30d": 20,
    "user_failed_logins_24h": 0,
    "user_max_spend_7d": 200.0,
}


class FeastFeatureClient:
    def __init__(self) -> None:
        repo_path = os.environ.get("FEATURE_REPO_PATH", "/app/feature_repo")
        self._store = FeatureStore(repo_path=repo_path)

    def get_user_features(self, user_id: str) -> dict[str, Any]:
        entity_df = pd.DataFrame(
            {
                "user_id": [user_id],
                "event_timestamp": [datetime.now(timezone.utc)],
            }
        )
        with FEATURE_FETCH_LATENCY.time():
            features = self._store.get_online_features(
                features=FEATURE_REFS,
                entity_rows=entity_df,
            ).to_dict()

        result = dict(DEFAULT_FEATURES)
        for key, values in features.items():
            if key in ("user_id", "event_timestamp"):
                continue
            val = values[0] if values else None
            if val is not None and pd.notna(val):
                result[key] = float(val) if "spend" in key or "max" in key or "avg" in key else int(val)
        return result
