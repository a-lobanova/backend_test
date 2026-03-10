# tests/test_payments_e2e.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.order import Order
from app.db.base import async_session_maker
import asyncio

client = TestClient(app)


@pytest.mark.asyncio
async def test_create_and_refund_payment():
    # --- создаем два заказа напрямую в БД ---
    async with async_session_maker() as session:
        async with session.begin():
            order1 = Order(amount=50, description="Order 1")
            order2 = Order(amount=50, description="Order 2")
            session.add_all([order1, order2])
            await session.flush()
            await session.refresh(order1)
            await session.refresh(order2)
            order1_id = order1.id
            order2_id = order2.id

    # --- вызываем REST API для создания платежей ---
    response1 = client.post(
        "/payments",
        json={"order_id": order1_id, "amount": 20, "payment_type": "ACQUIRING"},
    )
    response2 = client.post(
        "/payments",
        json={"order_id": order2_id, "amount": 30, "payment_type": "ACQUIRING"},
    )

    print(response1.status_code, response1.json())
    print(response2.status_code, response2.json())

    assert response1.status_code == 200
    assert response2.status_code == 200
    payment1 = response1.json()
    payment2 = response2.json()
    assert payment1["status"] == "COMPLETED"
    assert payment2["status"] == "COMPLETED"

    # --- проверяем REST API для возврата платежа ---
    refund_response = client.post(f"/payments/{order1_id}/refund")
    assert refund_response.status_code == 200
    refund_data = refund_response.json()
    assert refund_data["status"] == "REFUNDED"

    # --- проверяем, что повторный возврат не проходит ---
    refund_response2 = client.post(f"/payments/{order1_id}/refund")
    assert refund_response2.status_code == 400
