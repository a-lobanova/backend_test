# app/repositories/order_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderPaymentStatus


class OrderRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, order_id: int) -> Order | None:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        return result.scalars().first()

    async def lock(self, order_id: int) -> Order:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id).with_for_update()
        )
        return result.scalars().one()

    async def save(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def list_all(self) -> list[Order]:
        result = await self.db.execute(select(Order))
        return result.scalars().all()
