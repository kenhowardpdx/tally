"""add forecast settings to bank_accounts

Revision ID: e6a7f75ee398
Revises: dce3073b2c4e
Create Date: 2026-07-11 23:26:11.355961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6a7f75ee398'
down_revision: Union[str, Sequence[str], None] = 'dce3073b2c4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    cycle_type = sa.Enum('weekly', 'biweekly', 'monthly', 'semimonthly', name='cycle_type')
    cycle_type.create(op.get_bind())
    op.add_column('bank_accounts', sa.Column('forecast_starting_balance_cents', sa.BigInteger(), nullable=True))
    op.add_column('bank_accounts', sa.Column('forecast_income_per_cycle_cents', sa.BigInteger(), nullable=True))
    op.add_column('bank_accounts', sa.Column('forecast_cycle_type', cycle_type, nullable=True))
    op.add_column('bank_accounts', sa.Column('forecast_start_date', sa.Date(), nullable=True))
    op.add_column('bank_accounts', sa.Column('forecast_end_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bank_accounts', 'forecast_end_date')
    op.drop_column('bank_accounts', 'forecast_start_date')
    op.drop_column('bank_accounts', 'forecast_cycle_type')
    op.drop_column('bank_accounts', 'forecast_income_per_cycle_cents')
    op.drop_column('bank_accounts', 'forecast_starting_balance_cents')
    sa.Enum(name='cycle_type').drop(op.get_bind())
