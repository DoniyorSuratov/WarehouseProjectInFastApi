"""summa

Revision ID: c5406d7b05f3
Revises: 53ae367fc932
Create Date: 2024-03-06 17:52:30.789588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5406d7b05f3'
down_revision: Union[str, None] = '53ae367fc932'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'price')
    op.add_column('warehouse_data', sa.Column('price', sa.Float(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('warehouse_data', 'price')
    op.add_column('products', sa.Column('price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    # ### end Alembic commands ###