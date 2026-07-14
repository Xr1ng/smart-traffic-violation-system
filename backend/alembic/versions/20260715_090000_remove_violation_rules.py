"""Remove violation rule management table.

Revision ID: 20260715_090000
Revises: 20260714_140000
Create Date: 2026-07-15 09:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260715_090000"
down_revision: Union[str, Sequence[str], None] = "20260714_140000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "violation_rules" in inspector.get_table_names():
        indexes = {index["name"] for index in inspector.get_indexes("violation_rules")}
        if op.f("ix_violation_rules_rule_code") in indexes:
            op.drop_index(op.f("ix_violation_rules_rule_code"), table_name="violation_rules")
        op.drop_table("violation_rules")


def downgrade() -> None:
    if "violation_rules" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "violation_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_code", sa.String(length=32), nullable=False),
        sa.Column("violation_type", sa.String(length=32), nullable=False),
        sa.Column("rule_type", sa.String(length=32), nullable=False),
        sa.Column("params", sa.String(length=512), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_violation_rules_rule_code"),
        "violation_rules",
        ["rule_code"],
        unique=True,
    )
