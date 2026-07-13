"""add roles.description, roles.permissions and cases.ai_result_json

Revision ID: 9a3b5c7d1e2f
Revises: 8e5d0a2b4c6f
Create Date: 2026-07-13 02:04:08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '9a3b5c7d1e2f'
down_revision: Union[str, None] = '8e5d0a2b4c6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # roles.description
    try:
        op.add_column('roles', sa.Column('description', sa.String(255), nullable=True))
    except Exception:
        pass  # 字段已存在
    # roles.permissions
    try:
        op.add_column('roles', sa.Column('permissions', sa.String(512), nullable=True))
    except Exception:
        pass
    # cases.ai_result_json
    try:
        op.add_column('cases', sa.Column('ai_result_json', sa.String(4096), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_column('cases', 'ai_result_json')
    except Exception:
        pass
    try:
        op.drop_column('roles', 'permissions')
    except Exception:
        pass
    try:
        op.drop_column('roles', 'description')
    except Exception:
        pass
