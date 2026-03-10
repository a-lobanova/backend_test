# bank_api.py


from pydantic import BaseModel
from datetime import datetime
from typing import Literal


# --- acquiring_start ---
class AcquiringStartRequest(BaseModel):
    order_id: int
    amount: float


class AcquiringStartResponse(BaseModel):
    bank_payment_id: str  # UUID


# --- acquiring_check ---
class AcquiringCheckRequest(BaseModel):
    bank_payment_id: str


class AcquiringCheckResponse(BaseModel):
    bank_payment_id: str
    amount: float
    status: Literal["SUCCESS", "FAILED", "PENDING"]
    paid_at: datetime
