# tests/test_payments.py
import asyncio
import uuid
import pytest

from app.db.base import async_session_maker
from app.models.order import Order, OrderPaymentStatus
from app.models.payment import PaymentOperation, PaymentStatus
from app.services.payment_service import PaymentService
from app.repositories import OrderRepository, PaymentRepository, BankPaymentRepository


class FakeBankClient:
    async def acquiring_start(self, order_id, amount):
        return str(uuid.uuid4())

    async def acquiring_check(self, bank_payment_id):
        return {
            "bank_payment_id": bank_payment_id,
            "amount": 50,
            "status": "SUCCESS",
            "paid_at": "2026-03-09T10:00:00",
        }


async def test_payment_flow():
    async with async_session_maker() as db:
        async with db.begin():
            order_repo = OrderRepository(db)
            payment_repo = PaymentRepository(db)
            bank_payment_repo = BankPaymentRepository(db)
            bank_client = FakeBankClient()

            payment_service = PaymentService(
                order_repo, payment_repo, bank_payment_repo, bank_client, db
            )

            # --- Создаем заказ ---
            order = Order(amount=100, description="Test order")
            db.add(order)
            await db.flush()
            await db.refresh(order)

            # Проверяем, что заказ существует
            fetched_order = await order_repo.get(order.id)
            assert fetched_order is not None, f"Order {order.id} should exist"
            print(f"Order {order.id} exists, initial status: {fetched_order.status}")

            # --- Создаем платеж CASH ---
            payment1 = await payment_service.create_payment(
                order_id=order.id, amount=20, payment_type="CASH"
            )
            await db.refresh(order)
            print(
                f"Order {order.id} status after CASH payment: {order.status}, "
                f"Payment status: {payment1.status}, operation: {payment1.operation}"
            )
            assert payment1.status == PaymentStatus.SUCCESS
            assert payment1.operation == PaymentOperation.DEPOSIT
            assert order.status == OrderPaymentStatus.PARTIALLY_PAID

            # --- Создаем платеж ACQUIRING (PENDING) ---
            payment2 = await payment_service.create_payment(
                order_id=order.id, amount=30, payment_type="ACQUIRING"
            )
            await db.refresh(order)

            # --- Проверяем статус и операцию ---
            print(
                f"Order {order.id} status after ACQUIRING payment: {order.status}, "
                f"Payment status: {payment2.status}, operation: {payment2.operation}"
            )
            assert payment2.status == PaymentStatus.PENDING
            assert payment2.operation == PaymentOperation.DEPOSIT
            assert order.status == OrderPaymentStatus.PARTIALLY_PAID

            # --- Проверяем, что BankPayment был создан ---
            bank_payment = await bank_payment_repo.get_by_payment(payment2.id)
            print(
                f"BankPayment for payment {payment2.id}: status={bank_payment.status}, "
                f"bank_payment_id={bank_payment.bank_payment_id}"
            )
            assert bank_payment is not None
            assert bank_payment.status == "PENDING"

            # --- Попытка сделать платеж при PENDING платежах ---
            try:
                # --- Создаем платеж CASH ---
                payment3 = await payment_service.create_payment(
                    order_id=order.id, amount=20, payment_type="CASH"
                )
                await db.refresh(order)
            except Exception as e:
                print(f"Payment blocked as expected: {e}")
                assert "some payments are still pending" in str(e)

            # --- Попытка сделать возврат при PENDING платежах ---
            try:
                await payment_service.refund_payment(order.id)
            except Exception as e:
                print(f"Refund blocked as expected: {e}")
                assert "some payments are still pending" in str(e)

            # --- Синхронизация платежа с банком ---
            await payment_service.sync_bank_payment(payment2.id)

            payment2 = await payment_repo.get(payment2.id)
            await db.refresh(order)

            print(
                f"Order {order.id} status after bank sync: {order.status}, "
                f"Payment status: {payment2.status}"
            )

            assert payment2.status == PaymentStatus.SUCCESS

            # Обновляем статус заказа после успешного ACQUIRING
            await payment_service._update_order_payment_status(order)
            await db.refresh(order)
            print(f"Order {order.id} status after ACQUIRING SUCCESS: {order.status}")
            assert (
                order.status == OrderPaymentStatus.PARTIALLY_PAID
                or order.status == OrderPaymentStatus.PAID
            )

            # --- Делаем возврат после успешных платежей ---
            refund = await payment_service.refund_payment(order.id)
            await db.refresh(order)
            print(
                f"Order {order.id} status after REFUND: {order.status}, "
                f"Refund status: {refund.status}, amount: {refund.amount}, operation: {refund.operation}"
            )
            assert refund.status == PaymentStatus.SUCCESS
            assert refund.operation == PaymentOperation.REFUND
            assert order.status == OrderPaymentStatus.UNPAID


if __name__ == "__main__":
    asyncio.run(test_payment_flow())
