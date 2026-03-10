from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):

    order_id: int
    amount: float
    payment_type: str
