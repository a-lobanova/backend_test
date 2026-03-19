import pytest
from app.models.payment import PaymentStatus, PaymentOperation
from app.models.order import OrderPaymentStatus
from app.repositories import OrderRepository
from app.db.base import async_session_maker


@pytest.mark.asyncio
async def test_cash_payment(payment_service, create_order):
    order_id = await create_order()

    payment = await payment_service.create_payment(order_id, 50, "CASH")

    async with async_session_maker() as session:
        order = await OrderRepository(session).get(order_id)

        assert payment.status == PaymentStatus.SUCCESS
        assert payment.operation == PaymentOperation.DEPOSIT
        assert order.status == OrderPaymentStatus.PARTIALLY_PAID
