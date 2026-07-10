"""add intake description and vehicle unbinding

Revision ID: 8e5d0a2b4c6f
Revises: 7d4c9f1a2b3e
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8e5d0a2b4c6f"
down_revision: Union[str, Sequence[str], None] = "7d4c9f1a2b3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "intake_events",
        sa.Column("description", sa.String(length=512), nullable=True),
    )
    with op.batch_alter_table("vehicles") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM vehicles WHERE owner_id IS NULL"))
    with op.batch_alter_table("vehicles") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
    op.drop_column("intake_events", "description")
