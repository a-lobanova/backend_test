# bank_client.py
import httpx
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

    BASE_URL = "https://bank.api"

    async def acquiring_start(self, order_id: int, amount: float) -> str:
        # Используем Pydantic модель для запроса
        payload = AcquiringStartRequest(order_id=order_id, amount=amount)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/acquiring_start", json=payload.dict(), timeout=5
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
                    f"{self.BASE_URL}/acquiring_check", json=payload.dict(), timeout=5
                )

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
