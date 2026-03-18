# app/api/routes/orders.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.models.order import Order
from app.models.order import OrderPaymentStatus
from app.schemas.order import CreateOrderRequest, OrderResponse

from app.api.dependencies import get_order_repo
from app.repositories import OrderRepository

router = APIRouter(prefix="/orders", tags=["orders"])


# --- роутеры ---
@router.post("/", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    order_repo: OrderRepository = Depends(get_order_repo),
):
    order = Order(amount=request.amount, description=request.description)
    await order_repo.save(order)  # метод save() с flush+refresh внутри
    await order_repo.db.commit()  # to do - OrderService
    return OrderResponse(
        id=order.id,
        amount=order.amount,
        description=order.description,
        status=order.status.value,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    order_repo: OrderRepository = Depends(get_order_repo),
):
    order = await order_repo.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        id=order.id,
        amount=order.amount,
        description=order.description,
        status=order.status.value,
    )


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    order_repo: OrderRepository = Depends(get_order_repo),
):
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
