from sqlalchemy import BigInteger, DateTime, func, Numeric, String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
import enum
import decimal
from app.db.base import Base


class BankPayment(Base):
    __tablename__ = "bank_payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)
    bank_payment_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    paid_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    payment = relationship("Payment", back_populates="bank_payment")
