# app/api/routes/orders.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.repositories import OrderRepository
from app.models.order import Order, OrderPaymentStatus
from app.db.base import async_session_maker

router = APIRouter()


# Pydantic-схема для запроса на создание заказа
class CreateOrderRequest(BaseModel):
    amount: float
    description: str


# Pydantic-схема для ответа о заказе
class OrderResponse(BaseModel):
    id: int
    amount: float
    description: str
    status: str


@router.post("/orders", response_model=OrderResponse)
async def create_order(request: CreateOrderRequest):
    async with async_session_maker() as session:
        async with session.begin():
            order_repo = OrderRepository(session)
            order = Order(amount=request.amount, description=request.description)
            session.add(order)
            await session.flush()
            await session.refresh(order)
            return OrderResponse(
                id=order.id,
                amount=order.amount,
                description=order.description,
                status=order.status.value,
            )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int):
    async with async_session_maker() as session:
        order_repo = OrderRepository(session)
        order = await order_repo.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return OrderResponse(
            id=order.id,
            amount=order.amount,
            description=order.description,
            status=order.status.value,
        )


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders():
    async with async_session_maker() as session:
        order_repo = OrderRepository(session)
        orders = await order_repo.list_all()
        return [
            OrderResponse(
                id=o.id,
                amount=o.amount,
                description=o.description,
                status=o.status.value,
            )
            for o in orders
        ]
