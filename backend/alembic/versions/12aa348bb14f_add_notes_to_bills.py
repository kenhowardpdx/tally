"""add notes to bills

Revision ID: 12aa348bb14f
Revises: e6a7f75ee398
Create Date: 2026-07-12 13:02:59.853557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12aa348bb14f'
down_revision: Union[str, Sequence[str], None] = 'e6a7f75ee398'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bills', sa.Column('notes', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bills', 'notes')
