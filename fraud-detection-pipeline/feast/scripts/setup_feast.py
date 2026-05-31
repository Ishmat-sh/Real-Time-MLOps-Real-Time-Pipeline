#!/usr/bin/env python3
"""Seed offline feature data, apply Feast registry, and materialize to Redis."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from feast import FeatureStore

REPO_PATH = Path(os.environ.get("FEAST_REPO", "/app/feature_repo"))
DATA_DIR = REPO_PATH / "data"
NUM_USERS = 500


def generate_user_stats() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(NUM_USERS):
        user_id = f"user_{i:04d}"
        rows.append(
            {
                "user_id": user_id,
                "event_timestamp": now,
                "created": now,
                "user_avg_spend_30d": float(rng.uniform(20, 400)),
                "user_tx_count_30d": int(rng.integers(5, 120)),
                "user_failed_logins_24h": int(rng.integers(0, 5)),
                "user_max_spend_7d": float(rng.uniform(50, 800)),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    stats = generate_user_stats()
    stats_path = DATA_DIR / "user_stats.parquet"
    stats.to_parquet(stats_path, index=False)
    print(f"Wrote {len(stats)} user stat rows to {stats_path}")

    sys.path.insert(0, str(REPO_PATH))
    from entities import user  # noqa: E402
    from features import user_stats_fv  # noqa: E402

    store = FeatureStore(repo_path=str(REPO_PATH))
    store.apply([user, user_stats_fv])

    end = datetime.now(timezone.utc)
    start = end - pd.Timedelta(days=1)
    store.materialize(start_date=start.to_pydatetime(), end_date=end.to_pydatetime())
    print("Feast materialization complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
