#!/usr/bin/env python3
"""Consume raw transactions from Redpanda and score via the inference API."""

from __future__ import annotations

import json
import os
import signal
import sys
import time

import httpx
from kafka import KafkaConsumer

running = True


def shutdown(*_: object) -> None:
    global running
    running = False


def main() -> None:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP", "localhost:19092")
    topic = os.environ.get("KAFKA_TOPIC", "raw-transactions")
    group = os.environ.get("KAFKA_GROUP", "fraud-scoring-consumer")
    inference_url = os.environ.get("INFERENCE_URL", "http://localhost:8000/predict")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        group_id=group,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    client = httpx.Client(timeout=10.0)
    processed = 0
    flagged = 0
    errors = 0

    print(f"Consuming {topic} -> {inference_url}")

    while running:
        records = consumer.poll(timeout_ms=1000, max_records=100)
        for _partition, messages in records.items():
            for msg in messages:
                tx = msg.value
                try:
                    resp = client.post(inference_url, json=tx)
                    resp.raise_for_status()
                    result = resp.json()
                    processed += 1
                    if result["status"] == "flagged":
                        flagged += 1
                        print(
                            f"FRAUD ALERT tx={result['transaction_id']} "
                            f"p={result['fraud_probability']} latency={result['latency_ms']}ms"
                        )
                except httpx.HTTPError as exc:
                    errors += 1
                    if errors <= 5 or errors % 100 == 0:
                        print(f"Scoring error: {exc}", file=sys.stderr)
                except Exception as exc:
                    errors += 1
                    print(f"Unexpected error: {exc}", file=sys.stderr)

        if processed and processed % 1000 == 0:
            print(f"Processed={processed} flagged={flagged} errors={errors}")

    client.close()
    consumer.close()
    print("Consumer stopped.")


if __name__ == "__main__":
    main()
