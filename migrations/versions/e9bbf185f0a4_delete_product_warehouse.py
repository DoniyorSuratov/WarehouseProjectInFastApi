"""delete product warehouse

Revision ID: e9bbf185f0a4
Revises: eac8f2eb3106
Create Date: 2024-03-07 15:08:02.442380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9bbf185f0a4'
down_revision: Union[str, None] = 'eac8f2eb3106'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('deleted_products_warehouse', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'deleted_products_warehouse', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'deleted_products_warehouse', type_='foreignkey')
    op.drop_column('deleted_products_warehouse', 'user_id')
    # ### end Alembic commands ###
