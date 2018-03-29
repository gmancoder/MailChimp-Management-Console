"""empty message

Revision ID: 7cf0d4936f
Revises: 9f32ff3be0b
Create Date: 2016-11-17 13:11:56.444150

"""

# revision identifiers, used by Alembic.
revision = '7cf0d4936f'
down_revision = '9f32ff3be0b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('export_definition', sa.Column('target_list_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'export_definition', 'list', ['target_list_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'export_definition', type_='foreignkey')
    op.drop_column('export_definition', 'target_list_id')
    ### end Alembic commands ###
