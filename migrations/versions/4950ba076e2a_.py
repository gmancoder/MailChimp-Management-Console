"""empty message

Revision ID: 4950ba076e2a
Revises: 3aa86c508454
Create Date: 2016-12-01 11:23:20.221165

"""

# revision identifiers, used by Alembic.
revision = '4950ba076e2a'
down_revision = '3aa86c508454'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('segment_condition', sa.Column('type', sa.String(length=50), nullable=True))
    op.drop_column('segment_condition', 'merge_type')
    op.drop_column('segment_condition', 'condition_type')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('segment_condition', sa.Column('condition_type', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('segment_condition', sa.Column('merge_type', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.drop_column('segment_condition', 'type')
    ### end Alembic commands ###
