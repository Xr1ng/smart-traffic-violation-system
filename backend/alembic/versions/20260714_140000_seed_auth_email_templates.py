"""Seed required authentication email templates.

Revision ID: 20260714_140000
Revises: 20260714_130000
Create Date: 2026-07-14 14:00:00
"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260714_140000"
down_revision: Union[str, Sequence[str], None] = "20260714_130000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AUTH_EMAIL_TEMPLATES = {
    "register_email_code": (
        "【交通违章智能管理平台】注册验证码",
        "您的注册验证码是 {code}，{expires_minutes} 分钟内有效。请勿向他人泄露。",
    ),
    "password_reset_email_code": (
        "【交通违章智能管理平台】密码重置验证码",
        "您的密码重置验证码是 {code}，{expires_minutes} 分钟内有效。若非本人操作，请忽略。",
    ),
}


def upgrade() -> None:
    connection = op.get_bind()
    templates = sa.table(
        "notification_templates",
        sa.column("code", sa.String(32)),
        sa.column("channel", sa.String(16)),
        sa.column("subject_template", sa.String(255)),
        sa.column("body_template", sa.Text()),
        sa.column("status", sa.String(16)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    existing_codes = set(connection.scalars(
        sa.select(templates.c.code).where(
            templates.c.code.in_(AUTH_EMAIL_TEMPLATES)
        )
    ))
    now = datetime.now(timezone.utc)
    for code, (subject, body) in AUTH_EMAIL_TEMPLATES.items():
        if code in existing_codes:
            continue
        connection.execute(templates.insert().values(
            code=code,
            channel="email",
            subject_template=subject,
            body_template=body,
            status="enabled",
            created_at=now,
        ))


def downgrade() -> None:
    # Templates are operational data and may have been customized after upgrade.
    pass
