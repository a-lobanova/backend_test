import asyncio
from app.db.base import async_session_maker
from app.models import Order, Payment
from app.models.order import OrderPaymentStatus


async def print_orders_and_payments():
    async with async_session_maker() as session:
        # Получаем все заказы
        orders = await session.execute(Order.__table__.select().order_by(Order.id))
        orders = orders.fetchall()

        if not orders:
            print("No orders found.")
            return

        for order_row in orders:
            order = order_row._mapping  # SQLAlchemy row -> dict-like
            print(
                f"Order {order['id']}: amount={order['amount']}, status={order['status']}, description='{order['description']}'"
            )

            # Получаем все платежи для этого заказа
            payments = await session.execute(
                Payment.__table__.select()
                .where(Payment.order_id == order["id"])
                .order_by(Payment.id)
            )
            payments = payments.fetchall()

            if payments:
                for payment_row in payments:
                    payment = payment_row._mapping
                    print(
                        f"  Payment {payment['id']}: amount={payment['amount']}, status={payment['status']}, type={payment['type']}"
                    )
            else:
                print("  No payments for this order.")
        print("✅ Done.")


if __name__ == "__main__":
    asyncio.run(print_orders_and_payments())
