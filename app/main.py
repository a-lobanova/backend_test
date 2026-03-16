# app/main.py
from fastapi import FastAPI
from app.api.routes import payments, orders  # импортируем твои роутеры

app = FastAPI(title="Payment Service")

# подключаем роутеры
app.include_router(orders.router, prefix="", tags=["orders"])
app.include_router(payments.router, prefix="", tags=["payments"])  # роутеры платежей


# если хочешь, можно добавить root-эндпоинт для проверки
@app.get("/")
async def root():
    return {"message": "API is running"}
