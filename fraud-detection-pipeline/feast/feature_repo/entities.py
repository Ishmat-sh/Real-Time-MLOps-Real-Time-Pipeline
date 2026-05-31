from feast import Entity

user = Entity(
    name="user_id",
    join_keys=["user_id"],
    description="Credit card account holder",
)
