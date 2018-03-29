"""empty message

Revision ID: 53c42b7ee80c
Revises: 4723afb2fa5b
Create Date: 2016-11-23 10:24:47.005148

"""

# revision identifiers, used by Alembic.
revision = '53c42b7ee80c'
down_revision = '4723afb2fa5b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('email', sa.Column('last_sent', sa.TIMESTAMP(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('email', 'last_sent')
    ### end Alembic commands ###