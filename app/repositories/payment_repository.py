# app/repositories/payment_repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment, PaymentOperation, PaymentStatus


class PaymentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, payment_id: int) -> Payment | None:
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalars().first()

    async def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def sum_success_payments(self, order_id: int) -> float:
        total = await self.db.scalar(
            select(func.sum(Payment.amount)).where(
                Payment.order_id == order_id,
                Payment.status == PaymentStatus.SUCCESS,
                Payment.operation == PaymentOperation.DEPOSIT,
            )
        )
        return total or 0

    async def get_refund(self, order_id: int) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.operation == PaymentOperation.REFUND,  # по operation
                Payment.status == PaymentStatus.SUCCESS,
            )
        )
        return result.scalars().first()

    async def get_pending_payments(self, order_id: int) -> list[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.order_id == order_id)
            .where(Payment.status == PaymentStatus.PENDING)
            .where(Payment.operation == PaymentOperation.DEPOSIT)
        )
        return result.scalars().all()

    async def save(self, payment: Payment) -> Payment:
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment
