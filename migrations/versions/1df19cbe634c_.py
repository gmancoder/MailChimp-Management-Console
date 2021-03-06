"""empty message

Revision ID: 1df19cbe634c
Revises: 212739a64e07
Create Date: 2016-12-21 13:19:08.826502

"""

# revision identifiers, used by Alembic.
revision = '1df19cbe634c'
down_revision = '212739a64e07'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'list_subscriber_activity_parent_campaign_fkey', 'list_subscriber_activity', type_='foreignkey')
    op.drop_column('list_subscriber_activity', 'parent_campaign')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('list_subscriber_activity', sa.Column('parent_campaign', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(u'list_subscriber_activity_parent_campaign_fkey', 'list_subscriber_activity', 'campaign', ['parent_campaign'], ['id'])
    ### end Alembic commands ###
