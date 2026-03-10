# app/repositories/bank_payment_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.bank_payment import BankPayment
from app.models.payment import Payment


class BankPaymentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, bank_payment: BankPayment):
        self.db.add(bank_payment)
        await self.db.flush()
        await self.db.refresh(bank_payment)
        return bank_payment

    async def get_by_payment(self, payment_id: int) -> BankPayment | None:
        result = await self.db.execute(
            select(BankPayment).where(BankPayment.payment_id == payment_id)
        )
        return result.scalars().first()

    # --- Добавляем метод для PENDING платежей по заказу ---
    async def get_pending_by_order(self, order_id: int):
        result = await self.db.execute(
            select(BankPayment)
            .join(BankPayment.payment)  # <-- join по ORM-связи, не строке
            .where(BankPayment.status == "PENDING", Payment.order_id == order_id)
        )
        return result.scalars().all()

    async def save(self, bank_payment: BankPayment):
        self.db.add(bank_payment)
        await self.db.flush()
        await self.db.refresh(bank_payment)
        return bank_payment
