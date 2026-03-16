from decimal import Decimal
from app.models.order import OrderPaymentStatus, Order


class OrderStatusCalculator:

    def __init__(self, order_repo, payment_repo):
        self.order_repo = order_repo
        self.payment_repo = payment_repo

    async def calculate(self, order: Order):

        net_paid = await self.payment_repo.get_net_paid(order.id)

        if net_paid == Decimal("0.00"):
            order.status = OrderPaymentStatus.UNPAID
        elif net_paid < order.amount:
            order.status = OrderPaymentStatus.PARTIALLY_PAID
        else:
            order.status = OrderPaymentStatus.PAID

        await self.order_repo.save(order)

        return order
