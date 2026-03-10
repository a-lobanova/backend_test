"""initial

Revision ID: f6c7c74c7f62
Revises:
Create Date: 2026-03-09 15:15:41.421838

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f6c7c74c7f62"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Upgrade schema."""

    # создаем ENUM
    payment_operation = postgresql.ENUM("DEPOSIT", "REFUND", name="paymentoperation")

    payment_operation.create(op.get_bind())

    op.alter_column(
        "orders", "description", existing_type=sa.VARCHAR(length=255), nullable=True
    )

    op.add_column("payments", sa.Column("operation", payment_operation, nullable=False))


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("payments", "operation")

    payment_operation = postgresql.ENUM("DEPOSIT", "REFUND", name="paymentoperation")

    payment_operation.drop(op.get_bind())

    op.alter_column(
        "orders", "description", existing_type=sa.VARCHAR(length=255), nullable=False
    )

    op.create_table(
        "bank_payments",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("payment_id", sa.BIGINT(), nullable=False),
        sa.Column("bank_payment_id", sa.VARCHAR(length=255), nullable=False),
        sa.Column("status", sa.VARCHAR(length=50), nullable=False),
        sa.Column("paid_at", postgresql.TIMESTAMP(), nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###
