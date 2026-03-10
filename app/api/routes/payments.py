# api/routes/payments.py
# app/api/routes/payments.py
from fastapi import Depends, APIRouter, HTTPException
from app.services.payment_manager import PaymentManager
from app.repositories import OrderRepository, PaymentRepository, BankPaymentRepository
from app.integrations.bank_client import BankClient
from app.services.order_status_calculator import OrderStatusCalculator
from app.services.bank_sync_service import BankSyncService
from app.schemas.payment import CreatePaymentRequest

router = APIRouter()


def get_payment_service():
    # создаем все зависимости
    order_repo = OrderRepository()
    payment_repo = PaymentRepository()
    bank_payment_repo = BankPaymentRepository()
    bank_client = BankClient()
    order_status_calculator = OrderStatusCalculator()
    bank_sync_service = BankSyncService()
    return PaymentManager(
        order_repo=order_repo,
        payment_repo=payment_repo,
        bank_payment_repo=bank_payment_repo,
        bank_client=bank_client,
        order_status_calculator=order_status_calculator,
        bank_sync_service=bank_sync_service,
    )


@router.post("/payments")
async def create_payment(
    request: CreatePaymentRequest,
    payment_manager: PaymentManager = Depends(get_payment_service),
):
    try:
        payment = await payment_manager.create_payment(
            order_id=request.order_id,
            amount=request.amount,
            payment_type=request.payment_type,
        )
        return {"payment_id": payment.id, "status": payment.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payments/{order_id}/refund")
async def refund_payment(
    order_id: int,
    payment_manager: PaymentManager = Depends(get_payment_service),
):
    try:
        refund = await payment_manager.refund_payment(order_id)
        return {"refund_id": refund.id, "status": refund.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
