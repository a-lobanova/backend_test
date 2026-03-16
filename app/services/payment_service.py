# payment_service.py
# app/services/payment_service.py

from app.managers.payment_manager import PaymentManager
from app.models.payment import Payment, PaymentOperation, PaymentStatus
from app.models.bank_payment import BankPayment
from app.services.bank_sync_service import BankSyncService
from app.services.order_status_calculator import OrderStatusCalculator
from decimal import Decimal
from app.models.order import OrderPaymentStatus


class PaymentService:
    """Сервис, который оркестрирует сценарий оплаты"""

    def __init__(
        self,
        session_factory,
        bank_client,
        order_repo,
        payment_repo,
        bank_payment_repo,
        order_status_calculator,
    ):
        self.session_factory = session_factory
        self.bank_client = bank_client
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.bank_payment_repo = bank_payment_repo
        self.order_status_calculator = order_status_calculator

    async def create_payment(self, order_id: int, amount, payment_type: str):
        # --- 1. Синхронизация банка (своя транзакция) ---
        async with self.session_factory() as session:
            async with session.begin():
                bank_sync_service = BankSyncService(
                    bank_payment_repo=self.bank_payment_repo,
                    payment_repo=self.payment_repo,
                    bank_client=self.bank_client,
                    order_repo=self.order_repo,
                    order_status_calculator=self.order_status_calculator,
                )
                await bank_sync_service.sync_pending_for_order(order_id)

        # --- 2. Создание нового платежа (своя транзакция) ---
        async with self.session_factory() as session:
            async with session.begin():
                payment_manager = PaymentManager(
                    order_repo=self.order_repo,
                    payment_repo=self.payment_repo,
                    bank_payment_repo=self.bank_payment_repo,
                    bank_client=self.bank_client,
                    order_status_calculator=self.order_status_calculator,
                    bank_sync_service=bank_sync_service,  # если нужен
                )
                payment = await payment_manager.create_payment(
                    order_id, amount, payment_type
                )

                return payment

    async def refund_payment(self, payment_id: int):

        # --- 1. синхронизация платежа с банком ---
        async with self.session_factory() as session:
            async with session.begin():
                bank_sync_service = BankSyncService(
                    bank_payment_repo=self.bank_payment_repo,
                    payment_repo=self.payment_repo,
                    bank_client=self.bank_client,
                    order_repo=self.order_repo,
                    order_status_calculator=self.order_status_calculator,
                )

                await bank_sync_service.sync_bank_payment(payment_id)

        # --- 2. создание возврата ---
        async with self.session_factory() as session:
            async with session.begin():
                payment_manager = PaymentManager(
                    order_repo=self.order_repo,
                    payment_repo=self.payment_repo,
                    bank_payment_repo=self.bank_payment_repo,
                    bank_client=self.bank_client,
                    order_status_calculator=self.order_status_calculator,
                    bank_sync_service=bank_sync_service,
                )

                refund = await payment_manager.refund_payment(payment_id)

                return refund
