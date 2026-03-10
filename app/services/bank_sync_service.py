# services/bank_sync_service.py
from app.integrations.bank_client import PaymentNotFoundError
from app.models.payment import PaymentStatus


class BankSyncService:

    def __init__(
        self,
        bank_payment_repo,
        payment_repo,
        bank_client,
        order_repo,
        order_status_calculator,
    ):
        self.bank_payment_repo = bank_payment_repo
        self.payment_repo = payment_repo
        self.bank_client = bank_client
        self.order_repo = order_repo
        self.order_status_calculator = order_status_calculator

    async def sync_bank_payment(self, bank_payment_id: int):
        bank_payment = await self.bank_payment_repo.get_by_payment(bank_payment_id)

        try:
            bank_status = await self.bank_client.acquiring_check(
                bank_payment.bank_payment_id
            )
        except PaymentNotFoundError:
            bank_payment.status = "FAILED"
            payment = await self.payment_repo.get(bank_payment.payment_id)
            payment.status = PaymentStatus.FAILED

            await self.payment_repo.save(payment)
            await self.bank_payment_repo.save(bank_payment)

            order = await self.order_repo.get(payment.order_id)
            await self.order_status_calculator.calculate(order, self.payment_repo)
            return

        # FakeBankClient возвращает dict
        status = bank_status["status"]

        bank_payment.status = status

        payment = await self.payment_repo.get(bank_payment.payment_id)

        if status == "SUCCESS":
            payment.status = PaymentStatus.SUCCESS
        elif status == "FAILED":
            payment.status = PaymentStatus.FAILED
        elif status == "PENDING":
            payment.status = PaymentStatus.PENDING

        await self.payment_repo.save(payment)
        await self.bank_payment_repo.save(bank_payment)

        order = await self.order_repo.get(payment.order_id)
        await self.order_status_calculator.calculate(order, self.payment_repo)

    async def sync_pending_for_order(self, order_id: int):
        pending_bank_payments = await self.bank_payment_repo.get_pending_by_order(
            order_id
        )
        for bank_payment in pending_bank_payments:
            await self.sync_bank_payment(bank_payment.payment_id)

    async def sync_all_pending(self):
        pending_bank_payments = await self.bank_payment_repo.get_all_pending()
        for bank_payment in pending_bank_payments:
            await self.sync_bank_payment(bank_payment.payment_id)
