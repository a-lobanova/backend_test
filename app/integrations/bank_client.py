# bank_client.py
import httpx
import datetime
from datetime import datetime

from app.schemas.bank_api import (
    AcquiringStartRequest,
    AcquiringStartResponse,
    AcquiringCheckRequest,
    AcquiringCheckResponse,
)


class BankAPIError(Exception):
    pass


class PaymentNotFoundError(BankAPIError):
    """Ошибка, если банк не нашёл платеж"""

    pass


class BankClient:

    # BASE_URL = "https://bank.api"

    # Для тестов с локальным mock bank
    BASE_URL = "http://127.0.0.1:9000"

    async def acquiring_start(self, order_id: int, amount: float) -> str:
        # Используем Pydantic модель для запроса
        payload = AcquiringStartRequest(order_id=order_id, amount=amount)
        payload_dict = payload.model_dump()
        payload_dict["amount"] = float(payload_dict["amount"])

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/acquiring_start",
                    json=payload_dict,
                    timeout=5,
                )

            data = response.json()

            if response.status_code != 200:
                raise BankAPIError(f"Bank API error: {data}")

            if "error" in data:
                raise BankAPIError(data["error"])

            # Преобразуем через Pydantic модель ответа
            result = AcquiringStartResponse(**data)
            return result.bank_payment_id

        except httpx.RequestError as e:
            raise BankAPIError(f"Connection error: {e}")

    async def acquiring_check(self, bank_payment_id: str) -> AcquiringCheckResponse:
        # Pydantic модель запроса
        payload = AcquiringCheckRequest(bank_payment_id=bank_payment_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/acquiring_check",
                    json=payload.model_dump(),
                    timeout=5,
                )

            if response.status_code == 404:
                raise PaymentNotFoundError("Payment not found")

            data = response.json()
            if response.status_code != 200:
                raise BankAPIError(f"Bank API error: {data}")

            # Проверка ошибки “платеж не найден”
            if "error" in data:
                if "не найден" in data["error"].lower():
                    raise PaymentNotFoundError(data["error"])
                else:
                    raise BankAPIError(data["error"])

            # Возвращаем Pydantic объект ответа
            result = AcquiringCheckResponse(**data)
            return result

        except httpx.RequestError as e:
            raise BankAPIError(f"Connection error: {e}")
