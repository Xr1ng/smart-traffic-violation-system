"""add generic email verification support

Revision ID: 20260714_120000
Revises: b4f2c8d6a109
Create Date: 2026-07-14 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260714_120000"
down_revision: Union[str, Sequence[str], None] = "b4f2c8d6a109"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _validate_existing_user_emails() -> None:
    connection = op.get_bind()
    missing = connection.execute(sa.text(
        "SELECT COUNT(*) FROM users WHERE email IS NULL OR TRIM(email) = ''"
    )).scalar_one()
    duplicates = connection.execute(sa.text(
        "SELECT COUNT(*) FROM ("
        "SELECT LOWER(TRIM(email)) normalized FROM users "
        "WHERE email IS NOT NULL GROUP BY LOWER(TRIM(email)) HAVING COUNT(*) > 1"
        ") duplicate_emails"
    )).scalar_one()
    if missing or duplicates:
        raise RuntimeError(
            "用户邮箱数据不满足迁移要求：请先补齐空邮箱并清理重复邮箱"
        )


def upgrade() -> None:
    _validate_existing_user_emails()
    op.execute(sa.text("UPDATE users SET email = LOWER(TRIM(email))"))

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch_op.create_unique_constraint("uq_users_email", ["email"])
        batch_op.add_column(sa.Column(
            "auth_version", sa.Integer(), nullable=False, server_default="0"
        ))

    with op.batch_alter_table("notifications") as batch_op:
        batch_op.alter_column(
            "violation_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.add_column(sa.Column(
            "template_code", sa.String(length=32), nullable=True
        ))

    op.create_table(
        "email_verification_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "purpose IN ('register', 'password_reset')",
            name="ck_email_code_purpose",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_codes_email_purpose_created",
        "email_verification_codes",
        ["email", "purpose", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_email_codes_email_purpose_created",
        table_name="email_verification_codes",
    )
    op.drop_table("email_verification_codes")

    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_column("template_code")
        batch_op.alter_column(
            "violation_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("auth_version")
        batch_op.drop_constraint("uq_users_email", type_="unique")
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=255),
            nullable=True,
        )
