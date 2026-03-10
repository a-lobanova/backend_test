"""add status to orders

Revision ID: da8315adec2a
Revises: f6c7c74c7f62
Create Date: 2026-03-09 16:15:40.230730

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "da8315adec2a"
down_revision: Union[str, Sequence[str], None] = "f6c7c74c7f62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # создаём enum
    order_status_enum = sa.Enum(
        "UNPAID", "PARTIALLY_PAID", "PAID", name="orderpaymentstatus"
    )
    order_status_enum.create(op.get_bind(), checkfirst=True)

    # добавляем колонку с default='UNPAID' для существующих записей
    op.add_column(
        "orders",
        sa.Column("status", order_status_enum, nullable=False, server_default="UNPAID"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "status")
    sa.Enum(name="orderpaymentstatus").drop(op.get_bind(), checkfirst=True)
