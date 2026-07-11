"""make users email nullable

Revision ID: dce3073b2c4e
Revises: 9f979f5fb842
Create Date: 2026-07-11 10:13:04.507274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dce3073b2c4e'
down_revision: Union[str, Sequence[str], None] = '9f979f5fb842'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'email', existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'email', existing_type=sa.String(length=255), nullable=False)
