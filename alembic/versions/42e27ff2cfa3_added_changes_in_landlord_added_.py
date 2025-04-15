"""Added changes in landlord added password column

Revision ID: 42e27ff2cfa3
Revises: 80f9fad5ca14
Create Date: 2025-04-16 00:01:13.940100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42e27ff2cfa3'
down_revision: Union[str, None] = '80f9fad5ca14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('landlord', sa.Column('password', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('landlord', 'password')
    # ### end Alembic commands ###
