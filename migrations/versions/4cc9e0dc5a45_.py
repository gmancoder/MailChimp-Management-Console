"""empty message

Revision ID: 4cc9e0dc5a45
Revises: c1553712760
Create Date: 2017-01-04 11:01:30.107587

"""

# revision identifiers, used by Alembic.
revision = '4cc9e0dc5a45'
down_revision = 'c1553712760'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tracking', sa.Column('total_orders', sa.Integer(), nullable=True))
    op.add_column('tracking', sa.Column('total_revenue', sa.Float(), nullable=True))
    op.add_column('tracking', sa.Column('total_spent', sa.Float(), nullable=True))
    op.drop_column('tracking', 'percent_unique_clicks')
    op.drop_column('tracking', 'percent_unique_opens')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tracking', sa.Column('percent_unique_opens', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('tracking', sa.Column('percent_unique_clicks', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.drop_column('tracking', 'total_spent')
    op.drop_column('tracking', 'total_revenue')
    op.drop_column('tracking', 'total_orders')
    ### end Alembic commands ###
