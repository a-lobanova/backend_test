import asyncio
import uuid
import pytest

from app.db.base import async_session_maker
from app.models.order import Order, OrderPaymentStatus
from app.models.payment import PaymentOperation, PaymentStatus
from app.services.payment_manager import PaymentManager
from app.services.bank_sync_service import BankSyncService
from app.services.order_status_calculator import OrderStatusCalculator
from app.repositories import OrderRepository, PaymentRepository, BankPaymentRepository


class FakeBankClient:
    """Контролируемый fake клиент для синхронизации статусов платежей"""

    def __init__(self):
        self.status_map = {}

    async def acquiring_start(self, order_id, amount):
        bank_payment_id = str(uuid.uuid4())
        # при создании ACQUIRING платежа статус PENDING
        self.status_map[bank_payment_id] = "PENDING"
        return bank_payment_id

    async def acquiring_check(self, bank_payment_id):
        """Возвращаем текущий статус по bank_payment_id"""
        status = self.status_map.get(bank_payment_id, "PENDING")
        return {
            "bank_payment_id": bank_payment_id,
            "amount": 50,
            "status": status,
            "paid_at": "2026-03-09T10:00:00",
        }

    def set_status(self, bank_payment_id, status):
        """Можно вручную изменить статус для теста"""
        self.status_map[bank_payment_id] = status


@pytest.mark.asyncio
async def test_payment_manager_flow():
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

            # --- Создаём заказ ---
            order = Order(amount=100, description="Test order")
            db.add(order)
            await db.flush()
            await db.refresh(order)

            assert order.status == OrderPaymentStatus.UNPAID

            # --- CASH платеж ---
            payment1 = await manager.create_payment(order.id, 20, "CASH")
            await db.refresh(order)
            assert payment1.status == PaymentStatus.SUCCESS
            assert payment1.operation == PaymentOperation.DEPOSIT
            assert order.status == OrderPaymentStatus.PARTIALLY_PAID

            # --- ACQUIRING платеж (сначала PENDING) ---
            payment2 = await manager.create_payment(order.id, 30, "ACQUIRING")
            await db.refresh(order)
            assert payment2.status == PaymentStatus.PENDING
            assert order.status == OrderPaymentStatus.PARTIALLY_PAID

            # --- Проверяем, что BankPayment был создан ---
            bank_payment = await bank_payment_repo.get_by_payment(payment2.id)
            print(
                f"BankPayment for payment {payment2.id}: status={bank_payment.status}, "
                f"bank_payment_id={bank_payment.bank_payment_id}"
            )
            assert bank_payment is not None
            assert bank_payment.status == "PENDING"

            # bank_payment_id для синхронизации
            bank_client.set_status(bank_payment.bank_payment_id, "SUCCESS")

            # --- Синхронизация ACQUIRING платежа ---
            await bank_sync_service.sync_pending_for_order(order.id)
            await db.refresh(order)
            await db.refresh(payment2)
            assert payment2.status == PaymentStatus.SUCCESS

            # --- Синхронизация ACQUIRING платежа (банковский SUCCESS) ---
            bank_client.set_status(payment2.id, "SUCCESS")
            await bank_sync_service.sync_pending_for_order(order.id)
            await db.refresh(order)
            await db.refresh(payment2)
            assert payment2.status == PaymentStatus.SUCCESS
            assert order.status == OrderPaymentStatus.PARTIALLY_PAID

            # --- Доплачиваем заказ до полной суммы ---
            payment3 = await manager.create_payment(order.id, 50, "CASH")
            await db.refresh(order)

            assert payment3.status == PaymentStatus.SUCCESS
            assert order.status == OrderPaymentStatus.PAID

            # ---  Возврат ---
            refund3 = await manager.refund_payment(payment3.id)
            await db.refresh(order)
            assert refund3.status == PaymentStatus.SUCCESS

            refund2 = await manager.refund_payment(payment2.id)
            await db.refresh(order)
            assert refund2.status == PaymentStatus.SUCCESS

            refund1 = await manager.refund_payment(payment1.id)
            await db.refresh(order)
            assert refund1.status == PaymentStatus.SUCCESS

            assert order.status == OrderPaymentStatus.UNPAID

            # --- Попытка вернуть уже возвращенный платеж ---
            with pytest.raises(
                Exception, match=f"Payment {payment1.id} already refunded"
            ):
                await manager.refund_payment(payment1.id)
