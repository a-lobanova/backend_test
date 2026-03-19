import pytest
from app.models.payment import PaymentStatus
from app.models.order import OrderPaymentStatus
from app.repositories import OrderRepository, PaymentRepository, BankPaymentRepository
from app.db.base import async_session_maker


@pytest.mark.asyncio
async def test_acquiring_flow(payment_service, create_order, bank_client):
    order_id = await create_order()

    # создаем acquiring платеж
    payment = await payment_service.create_payment(order_id, 50, "ACQUIRING")

    async with async_session_maker() as session:
        order_repo = OrderRepository(session)
        bank_repo = BankPaymentRepository(session)

        order = await order_repo.get(order_id)
        bank_payment = await bank_repo.get_by_payment(payment.id)

        assert payment.status == PaymentStatus.PENDING
        assert order.status == OrderPaymentStatus.UNPAID
        assert bank_payment.status == "PENDING"

        # меняем статус в банке
        bank_client.set_status(bank_payment.bank_payment_id, "SUCCESS")

    # триггерим sync (пока через create_payment)
    await payment_service.create_payment(order_id, 0, "CASH")

    async with async_session_maker() as session:
        payment_db = await PaymentRepository(session).get(payment.id)
        order = await OrderRepository(session).get(order_id)

        assert payment_db.status == PaymentStatus.SUCCESS
        assert order.status == OrderPaymentStatus.PARTIALLY_PAID
