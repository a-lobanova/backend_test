import pytest
from app.models.payment import PaymentStatus
from app.models.order import OrderPaymentStatus
from app.repositories import OrderRepository
from app.db.base import async_session_maker


@pytest.mark.asyncio
async def test_refund_flow(payment_service, create_order):
    order_id = await create_order()

    # оплачиваем полностью
    p1 = await payment_service.create_payment(order_id, 40, "CASH")
    p2 = await payment_service.create_payment(order_id, 60, "CASH")

    # возвраты
    r1 = await payment_service.refund_payment(p1.id)
    r2 = await payment_service.refund_payment(p2.id)

    async with async_session_maker() as session:
        order = await OrderRepository(session).get(order_id)

        assert r1.status == PaymentStatus.SUCCESS
        assert r2.status == PaymentStatus.SUCCESS
        assert order.status == OrderPaymentStatus.UNPAID

    # повторный возврат
    with pytest.raises(Exception, match="already refunded"):
        await payment_service.refund_payment(p1.id)
