# tests/e2e/test_payments_e2e_sync.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.models.payment import Payment
from app.api.routes.payments import get_payment_manager


# --- мок PaymentManager ---
@pytest.fixture
def mock_payment_manager():
    manager = MagicMock()
    manager.create_payment = AsyncMock(return_value=Payment(id=1, status="COMPLETED"))
    return manager


# --- override зависимости ---
@pytest.fixture
def override_dependencies(mock_payment_manager):
    app.dependency_overrides[get_payment_manager] = lambda: mock_payment_manager
    yield
    app.dependency_overrides = {}


# --- синхронный тест через TestClient ---
def test_create_payment(override_dependencies):
    with TestClient(app) as client:
        response = client.post(
            "/payments",
            json={"order_id": 1, "amount": 20, "payment_type": "ACQUIRING"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["payment_id"] == 1
