# bank_api.py


from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
from decimal import Decimal


# --- acquiring_start ---
class AcquiringStartRequest(BaseModel):
    order_id: int
    amount: Decimal = Field(example="100.00")


class AcquiringStartResponse(BaseModel):
    bank_payment_id: str  # UUID


# --- acquiring_check ---
class AcquiringCheckRequest(BaseModel):
    bank_payment_id: str


class AcquiringCheckResponse(BaseModel):
    bank_payment_id: str
    amount: Decimal = Field(example="100.00")
    status: Literal["SUCCESS", "FAILED", "PENDING"]
    paid_at: datetime
