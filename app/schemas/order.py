# --- Pydantic-схемы ---

from pydantic import BaseModel, Field
from app.models.order import OrderPaymentStatus
from decimal import Decimal


class CreateOrderRequest(BaseModel):
    amount: Decimal = Field(example="100.00", json_schema_extra={"format": "decimal"})
    description: str


class OrderResponse(BaseModel):
    id: int
    amount: Decimal = Field(example="100.00")
    description: str
    status: OrderPaymentStatus
