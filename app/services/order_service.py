from decimal import Decimal


class OrderService:

    def __init__(self, order_repo, payment_repo):
        self.order_repo = order_repo
        self.payment_repo = payment_repo

    def recalculate_payment_status(self, order_id: int):

        order = self.order_repo.get(order_id)

        total_paid = self.payment_repo.sum_success_payments(order_id)

        if total_paid == 0:
            order.payment_status = "UNPAID"

        elif total_paid < order.amount:
            order.payment_status = "PARTIALLY_PAID"

        else:
            order.payment_status = "PAID"

        self.order_repo.save(order)

        return order
