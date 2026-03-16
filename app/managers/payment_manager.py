# payment_manager.py
# app/managers/payment_manager.py
from app.models.payment import Payment, PaymentOperation, PaymentStatus, PaymentType
from app.models.bank_payment import BankPayment
from app.services.bank_sync_service import BankSyncService
from app.services.order_status_calculator import OrderStatusCalculator
from decimal import Decimal
from app.models.order import OrderPaymentStatus


class PaymentManager:
    """Менеджер бизнес-логики платежей и возвратов"""

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
        self, order_id: int, amount: Decimal, payment_type: str
    ) -> Payment:
        """
        Создание платежа. Не занимается синхронизацией pending платежей с банком.
        PaymentService должен вызвать sync_pending_for_order до этого.
        """

        # Lock заказа и проверка статусов
        order = await self.order_repo.lock(order_id)

        if order.status == OrderPaymentStatus.PAID:
            raise Exception(f"Order {order.id} is already fully paid")

        net_paid = await self.payment_repo.get_net_paid(order_id)
        if net_paid + amount > order.amount:
            raise Exception("Payment exceeds order amount")

        # Создание нового платежа
        payment = Payment(
            order_id=order.id,
            amount=amount,
            type=payment_type,
            operation=PaymentOperation.DEPOSIT,
            status=PaymentStatus.CREATED,
        )
        await self.payment_repo.create(payment)

        # Обработка типа платежа
        bank_payment = None
        if payment_type == PaymentType.CASH:
            payment.status = PaymentStatus.SUCCESS
            await self.payment_repo.save(payment)

        elif payment_type == PaymentType.ACQUIRING:
            bank_id = await self.bank_client.acquiring_start(order.id, amount)
            bank_payment = BankPayment(
                payment_id=payment.id, bank_payment_id=bank_id, status="PENDING"
            )
            await self.bank_payment_repo.create(bank_payment)
            payment.status = PaymentStatus.PENDING
            await self.payment_repo.save(payment)

        # Пересчёт статуса заказа после изменения статуса платежа
        await self.order_status_calculator.calculate(order)

        return payment

    async def refund_payment(self, payment_id: int) -> Payment:
        """Создание возврата платежа"""

        payment = await self.payment_repo.get(payment_id)
        if not payment:
            raise Exception(f"Payment {payment_id} not found")

        order = await self.order_repo.lock(payment.order_id)

        # Синхронизация PENDING перед возвратом
        if payment.status == PaymentStatus.PENDING:
            await self.bank_sync_service.sync_bank_payment(payment_id)
            payment = await self.payment_repo.get(payment_id)

        if payment.operation != PaymentOperation.DEPOSIT:
            raise Exception(
                f"Payment {payment.id} is not a deposit and cannot be refunded"
            )

        if payment.status != PaymentStatus.SUCCESS:
            raise Exception(
                f"Payment {payment.id} cannot be refunded because it's not successful"
            )

        existing_refund = await self.payment_repo.get_refund_by_original(payment.id)
        if existing_refund:
            raise Exception(f"Payment {payment.id} already refunded")

        # Создание платежа возврата
        refund = Payment(
            order_id=order.id,
            amount=payment.amount,
            type=payment.type,
            operation=PaymentOperation.REFUND,
            status=PaymentStatus.SUCCESS,
            original_payment_id=payment.id,
        )
        await self.payment_repo.create(refund)

        # Пересчёт статуса заказа
        await self.order_status_calculator.calculate(order)

        return refund
