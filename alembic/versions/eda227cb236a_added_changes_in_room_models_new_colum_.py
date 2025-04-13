"""Added changes in room models new colum add rate

Revision ID: eda227cb236a
Revises: a9e2301435c6
Create Date: 2025-04-13 12:48:39.293471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eda227cb236a'
down_revision: Union[str, None] = 'a9e2301435c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('room', sa.Column('rate', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('room', 'rate')
    # ### end Alembic commands ###
