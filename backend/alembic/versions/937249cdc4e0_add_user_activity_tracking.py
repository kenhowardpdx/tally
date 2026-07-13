"""add user activity tracking

Revision ID: 937249cdc4e0
Revises: c889d199265f
Create Date: 2026-07-13 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '937249cdc4e0'
down_revision: Union[str, Sequence[str], None] = 'c889d199265f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'user_daily_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_date', sa.Date(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'activity_date', name='uq_user_daily_activity_user_date'),
    )
    op.create_index(
        op.f('ix_user_daily_activity_user_id'), 'user_daily_activity', ['user_id'], unique=False
    )
    op.create_index(
        'ix_user_daily_activity_activity_date', 'user_daily_activity', ['activity_date'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_user_daily_activity_activity_date', table_name='user_daily_activity')
    op.drop_index(op.f('ix_user_daily_activity_user_id'), table_name='user_daily_activity')
    op.drop_table('user_daily_activity')
    op.drop_column('users', 'last_active_at')
