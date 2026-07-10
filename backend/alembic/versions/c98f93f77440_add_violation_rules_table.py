"""add violation_rules table

Revision ID: c98f93f77440
Revises: e6b1a56b15ef
Create Date: 2026-07-10 14:20:34.501808

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'c98f93f77440'
down_revision: Union[str, Sequence[str], None] = 'e6b1a56b15ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """The merge revision owns the shared violation_rules DDL."""
    pass


def downgrade() -> None:
    pass
