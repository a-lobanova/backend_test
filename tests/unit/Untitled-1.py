# tests/unit/test_bank_client.py
import pytest
from unittest.mock import AsyncMock, patch
from app.integrations.bank_client import BankClient, BankAPIError, PaymentNotFoundError
from app.schemas.bank_api import AcquiringStartResponse, AcquiringCheckResponse


@pytest.mark.asyncio
async def test_acquiring_start_success():
    client = BankClient()

    mock_response = {"bank_payment_id": "BANK123"}

    # Мокаем httpx.AsyncClient.post
    async def mock_post(*args, **kwargs):
        class MockResp:
            status_code = 200

            def json(self_inner):
                return mock_response

        return MockResp()

    with patch("httpx.AsyncClient.post", new=mock_post):
        bank_payment_id = await client.acquiring_start(order_id=1, amount=100)
        assert bank_payment_id == "BANK123"


@pytest.mark.asyncio
async def test_acquiring_check_payment_not_found():
    client = BankClient()

    mock_response = {"error": "Платеж не найден"}

    async def mock_post(*args, **kwargs):
        class MockResp:
            status_code = 200

            def json(self_inner):
                return mock_response

        return MockResp()

    with patch("httpx.AsyncClient.post", new=mock_post):
        with pytest.raises(PaymentNotFoundError):
            await client.acquiring_check(bank_payment_id="BANK123")


@pytest.mark.asyncio
async def test_acquiring_check_success():
    client = BankClient()

    mock_response = {
        "bank_payment_id": "BANK123",
        "status": "COMPLETED",
        "amount": 100.0,
    }

    async def mock_post(*args, **kwargs):
        class MockResp:
            status_code = 200

            def json(self_inner):
                return mock_response

        return MockResp()

    with patch("httpx.AsyncClient.post", new=mock_post):
        result = await client.acquiring_check(bank_payment_id="BANK123")
        assert isinstance(result, AcquiringCheckResponse)
        assert result.status == "COMPLETED"
