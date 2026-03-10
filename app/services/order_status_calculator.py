from app.models.order import OrderPaymentStatus
from app.models.payment import PaymentStatus


class OrderStatusCalculator:

    @staticmethod
    async def calculate(order, payment_repo):
        total_deposit = await payment_repo.sum_success_payments(order.id)
        has_refund = await payment_repo.get_refund(order.id)

        if has_refund:
            order.status = OrderPaymentStatus.UNPAID
        elif total_deposit == 0:
            order.status = OrderPaymentStatus.UNPAID
        elif total_deposit < order.amount:
            order.status = OrderPaymentStatus.PARTIALLY_PAID
        else:
            order.status = OrderPaymentStatus.PAID

        await payment_repo.db.flush()
