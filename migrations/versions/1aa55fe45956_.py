"""empty message

Revision ID: 1aa55fe45956
Revises: 2be0bf9a5fc2
Create Date: 2016-12-30 10:06:57.572514

"""

# revision identifiers, used by Alembic.
revision = '1aa55fe45956'
down_revision = '2be0bf9a5fc2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'variate_campaign_email_id_fkey', 'variate_campaign', type_='foreignkey')
    op.drop_column('variate_campaign', 'email_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('variate_campaign', sa.Column('email_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(u'variate_campaign_email_id_fkey', 'variate_campaign', 'email', ['email_id'], ['id'])
    ### end Alembic commands ###
