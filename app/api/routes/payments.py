# app/api/routes/payments.py

from fastapi import Depends, APIRouter, HTTPException
from app.schemas.payment import CreatePaymentRequest, PaymentResponse
from app.api.dependencies import get_payment_service  # теперь получаем PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentResponse)
async def create_payment(
    request: CreatePaymentRequest,
    payment_service=Depends(get_payment_service),
):
    """
    Создание нового платежа.
    Сначала синхронизируются pending платежи с банком, потом создается новый платеж.
    """
    try:
        payment = await payment_service.create_payment(
            order_id=request.order_id,
            amount=request.amount,
            payment_type=request.payment_type,
        )

        return PaymentResponse(
            id=payment.id,
            status=(
                payment.status.value
                if hasattr(payment.status, "value")
                else payment.status
            ),
            amount=payment.amount,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: int,
    payment_service=Depends(get_payment_service),
):
    """
    Создание возврата для платежа.
    Сначала синхронизируется статус платежа с банком, если он был pending.
    """
    try:
        refund = await payment_service.refund_payment(payment_id)

        return PaymentResponse(
            id=refund.id,
            status=(
                refund.status.value
                if hasattr(refund.status, "value")
                else refund.status
            ),
            amount=refund.amount,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
