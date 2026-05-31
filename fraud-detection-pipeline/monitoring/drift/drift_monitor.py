#!/usr/bin/env python3
"""Compare production inference samples against training baseline using Evidently."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

BASELINE_PATH = Path(os.environ.get("BASELINE_PATH", "/app/data/baseline/training_features.parquet"))
SAMPLE_DIR = Path(os.environ.get("SAMPLE_DIR", "/app/drift_samples"))
SAMPLE_FILE = SAMPLE_DIR / "production_samples.jsonl"
REPORT_DIR = Path(os.environ.get("REPORT_DIR", "/app/drift_reports"))
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL_SECONDS", "120"))
DRIFT_THRESHOLD = float(os.environ.get("DRIFT_THRESHOLD", "0.25"))
MIN_SAMPLES = int(os.environ.get("MIN_SAMPLES", "200"))


def load_production_samples() -> pd.DataFrame:
    if not SAMPLE_FILE.exists():
        return pd.DataFrame()
    rows = []
    with SAMPLE_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    drop_cols = {"fraud_probability", "status"}
    return df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")


def run_drift_check() -> None:
    if not BASELINE_PATH.exists():
        print(f"Baseline not found: {BASELINE_PATH}")
        return

    current = load_production_samples()
    if len(current) < MIN_SAMPLES:
        print(f"Waiting for samples ({len(current)}/{MIN_SAMPLES})")
        return

    reference = pd.read_parquet(BASELINE_PATH)
    common = [c for c in reference.columns if c in current.columns]
    if not common:
        print("No overlapping feature columns for drift analysis.")
        return

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference[common], current_data=current[common].tail(5000))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    html_path = REPORT_DIR / f"drift_report_{ts}.html"
    report.save_html(str(html_path))

    result = report.as_dict()
    drift_share = 0.0
    for metric in result.get("metrics", []):
        if metric.get("metric") == "DatasetDriftMetric":
            drift_share = float(metric.get("result", {}).get("drift_share", 0) or 0)

    status = "DRIFT_DETECTED" if drift_share >= DRIFT_THRESHOLD else "STABLE"
    print(
        f"[{datetime.now(timezone.utc).isoformat()}] Drift check: "
        f"share={drift_share:.3f} threshold={DRIFT_THRESHOLD} status={status} report={html_path}"
    )
    if status == "DRIFT_DETECTED":
        print("ALERT: Data drift detected — trigger model retraining pipeline (simulated).")


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Drift monitor started (interval={CHECK_INTERVAL}s)")
    while True:
        try:
            run_drift_check()
        except Exception as exc:
            print(f"Drift check failed: {exc}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
