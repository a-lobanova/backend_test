# mock_bank.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import Literal
import uuid
import asyncio

import datetime
from datetime import datetime

app = FastAPI()


from app.schemas.bank_api import (
    AcquiringStartRequest,
    AcquiringStartResponse,
    AcquiringCheckRequest,
    AcquiringCheckResponse,
)

# храним состояние "платежей" в памяти
payments = {}


@app.get("/ping")
async def ping():
    return {"status": "ok"}


@app.post("/acquiring_start", response_model=AcquiringStartResponse)
async def acquiring_start(req: AcquiringStartRequest):
    bank_payment_id = str(uuid.uuid4())
    # Сохраняем платеж как PENDING
    payments[bank_payment_id] = {
        "order_id": req.order_id,
        "amount": req.amount,
        "status": "PENDING",
    }
    # имитация автоматического подтверждения через 3 секунды
    asyncio.create_task(confirm_payment(bank_payment_id))
    print("payments mock_bank acquiring_start", payments)
    return {"bank_payment_id": bank_payment_id}


async def confirm_payment(bank_payment_id: str):
    await asyncio.sleep(3)  # имитация задержки
    # случайно выбираем SUCCESS или FAILED (можно настроить)
    payments[bank_payment_id]["status"] = "SUCCESS"


@app.post("/acquiring_check", response_model=AcquiringCheckResponse)
async def acquiring_check(req: AcquiringCheckRequest):
    if req.bank_payment_id not in payments:
        print("mock_bank acquiring_check Платежа нет", payments)
        raise HTTPException(status_code=404, detail="payment not found")
    p = payments[req.bank_payment_id]
    return AcquiringCheckResponse(
        bank_payment_id=req.bank_payment_id,
        amount=Decimal(p["amount"]),
        status=p["status"],
        paid_at=datetime.now(),
    )
