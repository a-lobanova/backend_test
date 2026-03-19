import uuid
import pytest
import pytest_asyncio

from app.db.base import async_session_maker
from app.services.payment_service import PaymentService
from app.services.order_status_calculator import OrderStatusCalculator


class FakeBankStatus:
    def __init__(self, bank_payment_id, amount, status, paid_at):
        self.bank_payment_id = bank_payment_id
        self.amount = amount
        self.status = status
        self.paid_at = paid_at


class FakeBankClient:
    def __init__(self):
        self.status_map = {}

    async def acquiring_start(self, order_id, amount):
        bank_payment_id = str(uuid.uuid4())
        self.status_map[bank_payment_id] = "PENDING"
        return bank_payment_id

    async def acquiring_check(self, bank_payment_id):
        status = self.status_map.get(bank_payment_id, "PENDING")
        return FakeBankStatus(
            bank_payment_id=bank_payment_id,
            amount=50,
            status=status,
            paid_at="2026-03-09T10:00:00",
        )

    def set_status(self, bank_payment_id, status):
        self.status_map[bank_payment_id] = status


@pytest.fixture
def bank_client():
    return FakeBankClient()


@pytest.fixture
def payment_service(bank_client):
    return PaymentService(
        session_factory=async_session_maker,
        bank_client=bank_client,
        order_repo=None,
        payment_repo=None,
        bank_payment_repo=None,
        order_status_calculator=OrderStatusCalculator(None, None),
    )


@pytest_asyncio.fixture
async def create_order():
    from app.models.order import Order

    async def _create(amount=100):
        async with async_session_maker() as session:
            async with session.begin():
                order = Order(amount=amount, description="Test order")
                session.add(order)

            await session.refresh(order)
            return order.id

    return _create
