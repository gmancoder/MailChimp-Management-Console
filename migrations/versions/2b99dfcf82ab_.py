"""empty message

Revision ID: 2b99dfcf82ab
Revises: c28715c9232
Create Date: 2016-12-14 13:11:53.996148

"""

# revision identifiers, used by Alembic.
revision = '2b99dfcf82ab'
down_revision = 'c28715c9232'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('campaign', sa.Column('segment_id', sa.Integer(), nullable=True))
    op.drop_constraint(u'campaign_saved_segment_id_fkey', 'campaign', type_='foreignkey')
    op.create_foreign_key(None, 'campaign', 'segment', ['segment_id'], ['id'])
    op.drop_column('campaign', 'saved_segment_id')
    op.drop_column('campaign', 'segment_match')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('campaign', sa.Column('segment_match', sa.VARCHAR(length=3), autoincrement=False, nullable=True))
    op.add_column('campaign', sa.Column('saved_segment_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'campaign', type_='foreignkey')
    op.create_foreign_key(u'campaign_saved_segment_id_fkey', 'campaign', 'segment', ['saved_segment_id'], ['id'])
    op.drop_column('campaign', 'segment_id')
    ### end Alembic commands ###
