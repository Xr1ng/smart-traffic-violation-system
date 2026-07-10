"""merge duplicate violation rule heads"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d4c9f1a2b3e"
down_revision: Union[str, Sequence[str], None] = ("424e8489d6c7", "c98f93f77440")
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "violation_rules" not in sa.inspect(op.get_bind()).get_table_names():
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


def downgrade() -> None:
    if "violation_rules" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_index(
            op.f("ix_violation_rules_rule_code"), table_name="violation_rules"
        )
        op.drop_table("violation_rules")
