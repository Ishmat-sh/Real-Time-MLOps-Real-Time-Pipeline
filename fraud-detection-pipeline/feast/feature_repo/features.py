from datetime import timedelta

from feast import FeatureView, Field
from feast.types import Float32, Int64

from entities import user
from data_sources import user_stats_source

user_stats_fv = FeatureView(
    name="user_stats",
    entities=[user],
    ttl=timedelta(days=90),
    schema=[
        Field(name="user_avg_spend_30d", dtype=Float32),
        Field(name="user_tx_count_30d", dtype=Int64),
        Field(name="user_failed_logins_24h", dtype=Int64),
        Field(name="user_max_spend_7d", dtype=Float32),
    ],
    online=True,
    source=user_stats_source,
)
