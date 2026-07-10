"""add violation_rules table

Revision ID: 424e8489d6c7
Revises: 52bdc65fb503
Create Date: 2026-07-09 18:05:42.662760

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '424e8489d6c7'
down_revision: Union[str, Sequence[str], None] = '52bdc65fb503'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """The merge revision owns the shared violation_rules DDL."""
    pass


def downgrade() -> None:
    pass
