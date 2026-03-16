import pytest

from app.db.base import async_session_maker
from app.models.order import Order, OrderPaymentStatus
from app.models.payment import PaymentStatus, PaymentOperation
from app.services.payment_manager import PaymentManager
from app.services.bank_sync_service import BankSyncService
from app.services.order_status_calculator import OrderStatusCalculator
from app.repositories import OrderRepository, PaymentRepository, BankPaymentRepository


class FakeBankClient:
    async def acquiring_start(self, order_id, amount):
        return "fake_bank_id"

    async def acquiring_check(self, bank_payment_id):
        return {
            "bank_payment_id": bank_payment_id,
            "amount": 30,
            "status": "SUCCESS",
            "paid_at": "2026-03-09T10:00:00",
        }


@pytest.mark.asyncio
async def test_partial_payment_refund():
    async with async_session_maker() as db:
        async with db.begin():

            order_repo = OrderRepository(db)
            payment_repo = PaymentRepository(db)
            bank_payment_repo = BankPaymentRepository(db)

            bank_client = FakeBankClient()
            order_status_calculator = OrderStatusCalculator(order_repo, payment_repo)

            bank_sync_service = BankSyncService(
                bank_payment_repo,
                payment_repo,
                bank_client,
                order_repo,
                order_status_calculator,
            )

            manager = PaymentManager(
                order_repo,
                payment_repo,
                bank_payment_repo,
                bank_client,
                order_status_calculator,
                bank_sync_service,
            )

            # --- создаём заказ ---
            order = Order(amount=100, description="Test order")
            db.add(order)
            await db.flush()
            await db.refresh(order)

            assert order.status == OrderPaymentStatus.UNPAID

            # --- частичная оплата ---
            payment = await manager.create_payment(order.id, 30, "CASH")

            await db.refresh(order)

            assert payment.status == PaymentStatus.SUCCESS
            assert order.status == OrderPaymentStatus.PARTIALLY_PAID

            # --- возврат ---
            refund = await manager.refund_payment(payment.id)

            await db.refresh(order)

            assert refund.operation == PaymentOperation.REFUND
            assert refund.status == PaymentStatus.SUCCESS

            # возвращается только оплаченная часть
            assert refund.amount == 30

            # заказ снова неоплачен
            assert order.status == OrderPaymentStatus.UNPAID

            # заказ можно снова оплатить
            # --- попытка снова оплатить тот же заказ ---
            payment2 = await manager.create_payment(order.id, 50, "CASH")
            await db.refresh(order)

            assert payment2.status == PaymentStatus.SUCCESS
            assert order.status == OrderPaymentStatus.PARTIALLY_PAID
