# app/api/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.bank_client import BankClient

from app.managers.payment_manager import PaymentManager
from app.services.payment_service import PaymentService
from app.services.order_status_calculator import OrderStatusCalculator
from app.services.bank_sync_service import BankSyncService

from app.db.session import get_session
from app.repositories import OrderRepository, PaymentRepository, BankPaymentRepository


async def get_order_repo(
    session: AsyncSession = Depends(get_session),
) -> OrderRepository:
    return OrderRepository(session)


async def get_payment_repo(
    session: AsyncSession = Depends(get_session),
) -> PaymentRepository:
    return PaymentRepository(session)


async def get_bank_payment_repo(
    session: AsyncSession = Depends(get_session),
) -> BankPaymentRepository:
    return BankPaymentRepository(session)


async def get_payment_service(
    session: AsyncSession = Depends(get_session),
) -> PaymentService:
    """
    Создаёт PaymentService с отдельными транзакциями для:
    1. sync_pending платежей через BankSyncService
    2. создания нового платежа через PaymentManager
    """

    # Репозитории
    order_repo = OrderRepository(session)
    payment_repo = PaymentRepository(session)
    bank_payment_repo = BankPaymentRepository(session)

    # Клиент банка
    bank_client = BankClient()

    # Калькулятор статусов заказа
    order_status_calculator = OrderStatusCalculator(order_repo, payment_repo)

    # Сервис синхронизации с банком
    bank_sync_service = BankSyncService(
        bank_payment_repo=bank_payment_repo,
        payment_repo=payment_repo,
        bank_client=bank_client,
        order_repo=order_repo,
        order_status_calculator=order_status_calculator,
    )

    # Менеджер создания платежей
    payment_manager = PaymentManager(
        order_repo=order_repo,
        payment_repo=payment_repo,
        bank_payment_repo=bank_payment_repo,
        bank_client=bank_client,
        order_status_calculator=order_status_calculator,
        bank_sync_service=bank_sync_service,
    )

    # PaymentService: orchestration с разделением транзакций
    return PaymentService(
        session_factory=lambda: session,  # здесь передаём session_factory для новых транзакций
        bank_client=bank_client,
        order_repo=order_repo,
        payment_repo=payment_repo,
        bank_payment_repo=bank_payment_repo,
        order_status_calculator=order_status_calculator,
    )
