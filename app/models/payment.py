from sqlalchemy import BigInteger, DateTime, func, Numeric, String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
import enum
import decimal
from app.db.base import Base


class PaymentType(str, enum.Enum):
    CASH = "CASH"
    ACQUIRING = "ACQUIRING"


class PaymentOperation(enum.Enum):
    DEPOSIT = "DEPOSIT"
    REFUND = "REFUND"


class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    amount: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    operation: Mapped[PaymentOperation] = mapped_column(
        Enum(PaymentOperation), nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)
    original_payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id"), nullable=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    order = relationship("Order", back_populates="payments")
    bank_payment = relationship("BankPayment", back_populates="payment", uselist=False)
