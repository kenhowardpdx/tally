"""add enabled to windfalls

Revision ID: b88c09336fb3
Revises: 937249cdc4e0
Create Date: 2026-07-15 14:52:16.947239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b88c09336fb3'
down_revision: Union[str, Sequence[str], None] = '937249cdc4e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'windfalls',
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('windfalls', 'enabled')
