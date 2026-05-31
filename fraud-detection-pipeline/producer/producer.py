#!/usr/bin/env python3
"""Simulate live credit card transactions and publish to Redpanda."""

from __future__ import annotations

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from faker import Faker
from kafka import KafkaProducer

fake = Faker()
Faker.seed(42)

MERCHANT_CATEGORIES = {
    "grocery": 5411,
    "gas": 5541,
    "restaurant": 5812,
    "electronics": 5732,
    "travel": 4511,
    "online_retail": 5999,
    "atm": 6011,
    "luxury": 5699,
}

LOCATIONS = [
    "New York, US",
    "London, UK",
    "Toronto, CA",
    "San Francisco, US",
    "Paris, FR",
    "Tokyo, JP",
    "Sydney, AU",
    "Berlin, DE",
]


def build_transaction(user_pool: list[str]) -> dict:
    now = datetime.now(timezone.utc)
    category = random.choice(list(MERCHANT_CATEGORIES.keys()))
    amount = round(random.lognormvariate(3.2, 0.7), 2)
    if random.random() < 0.02:
        amount = round(amount * random.uniform(5, 20), 2)

    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": random.choice(user_pool),
        "timestamp": now.isoformat(),
        "amount": max(amount, 1.0),
        "merchant_category": category,
        "merchant_category_code": MERCHANT_CATEGORIES[category],
        "location": random.choice(LOCATIONS),
        "hour_of_day": now.hour,
        "is_weekend": 1 if now.weekday() >= 5 else 0,
        "distance_from_home_km": round(random.expovariate(1 / 25), 2),
    }


def main() -> None:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP", "localhost:19092")
    topic = os.environ.get("KAFKA_TOPIC", "raw-transactions")
    tps = float(os.environ.get("TRANSACTIONS_PER_SECOND", "50"))
    delay = 1.0 / max(tps, 0.1)

    user_pool = [f"user_{i:04d}" for i in range(500)]

    producer = KafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=5,
        linger_ms=5,
    )

    print(f"Publishing to {topic} @ {bootstrap} (~{tps} tx/s)")
    count = 0
    while True:
        tx = build_transaction(user_pool)
        producer.send(topic, value=tx, key=tx["user_id"].encode())
        count += 1
        if count % 500 == 0:
            print(f"Published {count} transactions (latest user={tx['user_id']}, amount={tx['amount']})")
        time.sleep(delay)


if __name__ == "__main__":
    main()
