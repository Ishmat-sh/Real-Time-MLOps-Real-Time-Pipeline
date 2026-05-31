from pydantic import BaseModel, Field


class Transaction(BaseModel):
    transaction_id: str
    user_id: str
    timestamp: str
    amount: float = Field(gt=0)
    merchant_category: str
    merchant_category_code: int = Field(ge=1000, le=9999)
    location: str
    hour_of_day: int = Field(ge=0, le=23)
    is_weekend: int = Field(ge=0, le=1)
    distance_from_home_km: float = Field(ge=0)


class PredictionResponse(BaseModel):
    transaction_id: str
    status: str
    fraud_probability: float
    latency_ms: float
