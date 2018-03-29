"""empty message

Revision ID: a6192eb2156
Revises: 4950ba076e2a
Create Date: 2016-12-13 10:53:18.501906

"""

# revision identifiers, used by Alembic.
revision = 'a6192eb2156'
down_revision = '4950ba076e2a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('export_definition', sa.Column('target_segment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'export_definition', 'segment', ['target_segment_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'export_definition', type_='foreignkey')
    op.drop_column('export_definition', 'target_segment_id')
    ### end Alembic commands ###
