# app/tasks/payment_tasks.py
import asyncio
from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.repositories.payment_repository import PaymentRepository
from app.services.bank_sync_service import BankSyncService
from app.repositories.bank_payment_repository import BankPaymentRepository
from app.repositories.order_repository import OrderRepository
from app.services.order_status_calculator import OrderStatusCalculator
from app.integrations.bank_client import BankClient


@celery_app.task(name="sync_payments")
def sync_payments():
    asyncio.run(_sync_payments())  # запускаем async функцию из sync task


async def _sync_payments():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            payment_repo = PaymentRepository(session)
            bank_payment_repo = BankPaymentRepository(session)
            order_repo = OrderRepository(session)
            bank_client = BankClient()
            order_status_calculator = OrderStatusCalculator(
                order_repo=order_repo, payment_repo=payment_repo
            )

            bank = BankSyncService(
                bank_payment_repo=bank_payment_repo,
                payment_repo=payment_repo,
                bank_client=bank_client,
                order_repo=order_repo,
                order_status_calculator=order_status_calculator,
            )

            pending_payments = await payment_repo.get_pending()

            for payment in pending_payments:
                print("sync_tasc", payment.id)
                try:
                    await bank.sync_bank_payment(payment.id)
                except Exception as e:
                    print(f"Error syncing payment {payment.id}: {e}")
