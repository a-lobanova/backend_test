from sqlalchemy import BigInteger, DateTime, func, Numeric, String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
import enum
import decimal
from app.db.base import Base


class OrderPaymentStatus(enum.Enum):
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    amount: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    status: Mapped[OrderPaymentStatus] = mapped_column(
        Enum(OrderPaymentStatus, name="orderpaymentstatus"),
        default=OrderPaymentStatus.UNPAID,
        nullable=False,
    )

    payments = relationship("Payment", back_populates="order")
