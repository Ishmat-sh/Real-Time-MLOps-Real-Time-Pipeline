from prometheus_client import Counter, Histogram

PREDICTIONS_TOTAL = Counter(
    "fraud_predictions_total",
    "Total fraud scoring requests",
    ["status"],
)

FRAUD_FLAGGED_TOTAL = Counter(
    "fraud_flagged_total",
    "Transactions flagged as fraudulent",
)

PREDICTION_LATENCY = Histogram(
    "fraud_prediction_latency_seconds",
    "End-to-end prediction latency",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

FEATURE_FETCH_LATENCY = Histogram(
    "feast_feature_fetch_seconds",
    "Feast online feature retrieval latency",
    buckets=(0.0005, 0.001, 0.005, 0.01, 0.05, 0.1),
)
