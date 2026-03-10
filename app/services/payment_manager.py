# app/services/payment_manager.py

from app.models.payment import Payment, PaymentOperation, PaymentStatus
from app.models.bank_payment import BankPayment
from app.services.bank_sync_service import BankSyncService
from app.services.order_status_calculator import OrderStatusCalculator


class PaymentManager:
    """Менеджер создания платежей и возвратов"""

    def __init__(
        self,
        order_repo,
        payment_repo,
        bank_payment_repo,
        bank_client,
        order_status_calculator: OrderStatusCalculator,
        bank_sync_service: BankSyncService,
    ):
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.bank_payment_repo = bank_payment_repo
        self.bank_client = bank_client
        self.order_status_calculator = order_status_calculator
        self.bank_sync_service = bank_sync_service

    async def create_payment(
        self, order_id: int, amount: float, payment_type: str
    ) -> Payment:
        # Синхронизация PENDING перед созданием нового платежа
        await self.bank_sync_service.sync_pending_for_order(order_id)

        order = await self.order_repo.lock(order_id)

        if order.status == order.status.PAID:
            raise Exception(f"Order {order.id} is already fully paid")

        pending_payments = await self.payment_repo.get_pending_payments(order_id)
        if pending_payments:
            raise Exception("Cannot do payment: some payments are still pending")

        total_paid = await self.payment_repo.sum_success_payments(order_id)
        if total_paid + amount > order.amount:
            raise Exception("Payment exceeds order amount")

        payment = Payment(
            order_id=order.id,
            amount=amount,
            type=payment_type,
            operation=PaymentOperation.DEPOSIT,
            status=PaymentStatus.CREATED,
        )
        await self.payment_repo.create(payment)

        # Обрабатываем тип платежа
        if payment_type == "CASH":
            payment.status = PaymentStatus.SUCCESS
            await self.payment_repo.save(
                payment
            )  # сохраняем сразу, чтобы калькулятор видел SUCCESS
            await self.payment_repo.db.flush()
        elif payment_type == "ACQUIRING":
            bank_id = await self.bank_client.acquiring_start(order.id, amount)
            bank_payment = BankPayment(
                payment_id=payment.id, bank_payment_id=bank_id, status="PENDING"
            )
            await self.bank_payment_repo.create(bank_payment)
            payment.status = PaymentStatus.PENDING
            await self.payment_repo.save(payment)

        # Пересчёт статуса заказа после изменения статуса платежа
        order = await self.order_repo.get(order_id)
        await self.order_status_calculator.calculate(order, self.payment_repo)

        return payment

    async def refund_payment(self, order_id: int) -> Payment:
        # Синхронизация PENDING перед созданием нового платежа
        await self.bank_sync_service.sync_pending_for_order(order_id)
        order = await self.order_repo.lock(order_id)

        existing_refund = await self.payment_repo.get_refund(order_id)
        if existing_refund:
            raise Exception(f"Order {order.id} already refunded")

        pending_payments = await self.payment_repo.get_pending_payments(order_id)
        if pending_payments:
            raise Exception("Cannot do refund: some payments are still pending")

        total_paid = await self.payment_repo.sum_success_payments(order_id)
        if total_paid <= 0:
            raise Exception("Nothing to refund")

        refund = Payment(
            order_id=order.id,
            amount=total_paid,
            type="CASH",
            operation=PaymentOperation.REFUND,
            status=PaymentStatus.SUCCESS,
        )
        await self.payment_repo.create(refund)
        await self.payment_repo.save(refund)
        await self.order_status_calculator.calculate(order, self.payment_repo)
        return refund
