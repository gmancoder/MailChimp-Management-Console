"""empty message

Revision ID: 9f32ff3be0b
Revises: 292b23279f
Create Date: 2016-11-16 14:48:55.382280

"""

# revision identifiers, used by Alembic.
revision = '9f32ff3be0b'
down_revision = '292b23279f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('import_definition', sa.Column('target_list_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'import_definition', 'list', ['target_list_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'import_definition', type_='foreignkey')
    op.drop_column('import_definition', 'target_list_id')
    ### end Alembic commands ###
