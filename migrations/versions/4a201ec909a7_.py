"""empty message

Revision ID: 4a201ec909a7
Revises: a6192eb2156
Create Date: 2016-12-14 11:21:21.318646

"""

# revision identifiers, used by Alembic.
revision = '4a201ec909a7'
down_revision = 'a6192eb2156'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('variate_campaign',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('winning_combination_id', sa.String(), nullable=True),
    sa.Column('winning_campaign_id', sa.String(), nullable=True),
    sa.Column('winner_criteria', sa.String(length=10), nullable=True),
    sa.Column('wait_time', sa.Integer(), nullable=True),
    sa.Column('test_size', sa.Integer(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.String(length=10), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('updated_by', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('variate_campaign_combination',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mailchimp_id', sa.String(length=100), nullable=True),
    sa.Column('variate_campaign_id', sa.Integer(), nullable=True),
    sa.Column('send_time', sa.TIMESTAMP(), nullable=True),
    sa.Column('subject_line', sa.String(length=200), nullable=True),
    sa.Column('from_name', sa.String(length=200), nullable=True),
    sa.Column('reply_to', sa.String(length=200), nullable=True),
    sa.Column('recipents', sa.Integer(), nullable=True),
    sa.Column('content_label', sa.String(length=200), nullable=True),
    sa.Column('html_content', sa.Text(), nullable=True),
    sa.Column('plain_text_content', sa.Text(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['variate_campaign_id'], ['variate_campaign.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('campaign',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mailchimp_id', sa.String(length=100), nullable=True),
    sa.Column('brand_id', sa.Integer(), nullable=True),
    sa.Column('folder_id', sa.Integer(), nullable=True),
    sa.Column('email_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('send_time', sa.TIMESTAMP(), nullable=True),
    sa.Column('content_type', sa.String(length=100), nullable=True),
    sa.Column('list_id', sa.Integer(), nullable=True),
    sa.Column('list_name', sa.String(length=200), nullable=True),
    sa.Column('segment_text', sa.String(length=200), nullable=True),
    sa.Column('recipient_count', sa.Integer(), nullable=True),
    sa.Column('saved_segment_id', sa.Integer(), nullable=True),
    sa.Column('segment_match', sa.String(length=3), nullable=True),
    sa.Column('subject_line', sa.String(length=200), nullable=True),
    sa.Column('from_name', sa.String(length=200), nullable=True),
    sa.Column('reply_to', sa.String(length=200), nullable=True),
    sa.Column('authenticate', sa.Boolean(), nullable=True),
    sa.Column('auto_footer', sa.Boolean(), nullable=True),
    sa.Column('inline_css', sa.Boolean(), nullable=True),
    sa.Column('template_id', sa.Integer(), nullable=True),
    sa.Column('track_opens', sa.Boolean(), nullable=True),
    sa.Column('track_clicks', sa.Boolean(), nullable=True),
    sa.Column('delivery_status_enabled', sa.Boolean(), nullable=True),
    sa.Column('can_cancel', sa.Boolean(), nullable=True),
    sa.Column('delivery_status', sa.String(length=200), nullable=True),
    sa.Column('emails_sent', sa.Integer(), nullable=True),
    sa.Column('emails_canceled', sa.Integer(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.String(length=10), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('updated_by', sa.String(length=10), nullable=True),
    sa.ForeignKeyConstraint(['brand_id'], ['brand.id'], ),
    sa.ForeignKeyConstraint(['email_id'], ['email.id'], ),
    sa.ForeignKeyConstraint(['folder_id'], ['folder.id'], ),
    sa.ForeignKeyConstraint(['list_id'], ['list.id'], ),
    sa.ForeignKeyConstraint(['saved_segment_id'], ['segment.id'], ),
    sa.ForeignKeyConstraint(['template_id'], ['template.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('campaign_segment_condition',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('campaign_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('op', sa.String(length=50), nullable=True),
    sa.Column('field', sa.String(length=100), nullable=True),
    sa.Column('value', sa.String(length=200), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaign.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('campaign_segment_condition')
    op.drop_table('campaign')
    op.drop_table('variate_campaign_combination')
    op.drop_table('variate_campaign')
    ### end Alembic commands ###
