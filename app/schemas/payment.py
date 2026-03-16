from pydantic import BaseModel, Field
from app.models.payment import PaymentType, PaymentStatus
from decimal import Decimal


class CreatePaymentRequest(BaseModel):

    order_id: int
    amount: Decimal = Field(example="100.00")
    payment_type: PaymentType


class PaymentResponse(BaseModel):
    id: int
    status: PaymentStatus
    amount: Decimal = Field(example="100.00")
