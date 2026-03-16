# app/repositories/payment_repository.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import Payment, PaymentOperation, PaymentStatus, PaymentType
import decimal
from decimal import Decimal


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

    async def sum_success_payments(self, order_id: int) -> decimal.Decimal:
        total = await self.db.scalar(
            select(func.sum(Payment.amount)).where(
                Payment.order_id == order_id,
                Payment.status == PaymentStatus.SUCCESS,
                Payment.operation == PaymentOperation.DEPOSIT,
            )
        )
        return total or decimal.Decimal("0.00")

    async def sum_success_refund(self, order_id: int) -> decimal.Decimal:
        total = await self.db.scalar(
            select(func.sum(Payment.amount)).where(
                Payment.order_id == order_id,
                Payment.status == PaymentStatus.SUCCESS,
                Payment.operation == PaymentOperation.REFUND,  # по operation
            )
        )
        return total or decimal.Decimal("0.00")

    async def get_pending_payments(self, order_id: int) -> list[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.order_id == order_id)
            .where(Payment.status == PaymentStatus.PENDING)
        )
        return result.scalars().all()

    async def has_pending_acquiring(self, order_id: int) -> bool:
        result = await self.db.execute(
            select(Payment.id)
            .where(Payment.order_id == order_id)
            .where(Payment.status == PaymentStatus.PENDING)
            .limit(1)
        )
        return result.scalar() is not None

    async def get_refund_by_original(self, original_payment_id: int) -> Payment | None:
        """Возвращает Payment с операцией REFUND для заданного исходного депозита, если такой существует"""
        stmt = select(Payment).where(
            Payment.original_payment_id == original_payment_id,
            Payment.operation == PaymentOperation.REFUND,
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def save(self, payment: Payment) -> Payment:
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def get_net_paid(self, order_id: int) -> Decimal:
        total_paid = await self.sum_success_payments(order_id)
        total_refund = await self.sum_success_refund(order_id)
        return total_paid - total_refund

    async def get_pending(self):
        stmt = select(Payment).where(Payment.status == PaymentStatus.PENDING)
        result = await self.db.execute(stmt)
        payments = result.scalars().all()
        return payments
