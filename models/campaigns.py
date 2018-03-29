#!/usr/bin/env python
from models.shared import db
import datetime

class Campaign(db.Model):
    __tablename__ = "campaign"
    id = db.Column(db.Integer, primary_key=True)
    mailchimp_id = db.Column(db.String(100))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    email_id = db.Column(db.Integer, db.ForeignKey("email.id"))
    segment_id = db.Column(db.Integer, db.ForeignKey("segment.id"))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    name = db.Column(db.String(200))
    type = db.Column(db.String(50), default="regular")
    status = db.Column(db.String(50), default="save")
    emails_sent = db.Column(db.Integer, default=0)
    send_time = db.Column(db.TIMESTAMP, nullable=True)
    content_type = db.Column(db.String(100))
    
    # Recipients
    segment_text = db.Column(db.Text)
    recipient_count = db.Column(db.Integer, default=0)
    
    # Settings
    subject_line = db.Column(db.String(200))
    from_name = db.Column(db.String(200))
    reply_to = db.Column(db.String(200))
    authenticate = db.Column(db.Boolean, default=True)
    auto_footer = db.Column(db.Boolean, default=True)
    inline_css = db.Column(db.Boolean, default=True)
    template_id = db.Column(db.Integer, db.ForeignKey("template.id"))
    
    # Tracking
    track_opens = db.Column(db.Boolean, default=True)
    track_clicks = db.Column(db.Boolean, default=True)
    
    # Delivery Status
    delivery_status_enabled = db.Column(db.Boolean)
    can_cancel = db.Column(db.Boolean)
    delivery_status = db.Column(db.String(200))
    ds_emails_sent = db.Column(db.Integer)
    ds_emails_canceled = db.Column(db.Integer)

    # Schedule
    schedule_time = db.Column(db.TIMESTAMP)

    # Activity
    activity = db.relationship("ListSubscriberActivity", backref="campaign", lazy="dynamic", cascade="all,delete")
    
    # Screen Filters
    is_user_initiated = db.Column(db.Boolean, default=False)
    is_rtm = db.Column(db.Boolean, default=False)
    
    # MMC Default
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class VariateCampaign(db.Model):
    __tablename__ = "variate_campaign"
    id = db.Column(db.Integer, primary_key=True)
    mailchimp_id = db.Column(db.String(100))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    segment_id = db.Column(db.Integer, db.ForeignKey("segment.id"))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    name = db.Column(db.String(200))
    status = db.Column(db.String(50), default="save")
    send_time = db.Column(db.TIMESTAMP, nullable=True)

    #Settings
    subject_line = db.Column(db.String(200))
    from_name = db.Column(db.String(200))
    reply_to = db.Column(db.String(200))
    schedule_time = db.Column(db.TIMESTAMP)

    #Variate Settings
    winning_combination_id = db.Column(db.String)
    winning_campaign_id = db.Column(db.String)
    winner_criteria = db.Column(db.String(10), default="opens")
    wait_time = db.Column(db.Integer, default=60)
    test_size = db.Column(db.Integer, default=10)
    test_type = db.Column(db.String, default="subject_line")
    test_combinations = db.Column(db.Integer, default=2)
    combinations = db.relationship("VariateCampaignCombination", lazy="dynamic", cascade="all,delete")
    activity = db.relationship("ListSubscriberActivity", backref="ab_test", lazy="dynamic", cascade="all,delete")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class VariateCampaignCombination(db.Model):
    __tablename__ = "variate_campaign_combination"
    id = db.Column(db.Integer, primary_key=True)
    variate_campaign_id = db.Column(db.Integer, db.ForeignKey("variate_campaign.id"))
    mailchimp_id = db.Column(db.String(50))
    email_id = db.Column(db.Integer, db.ForeignKey("email.id"))
    send_time = db.Column(db.TIMESTAMP, nullable=True)
    subject_line = db.Column(db.String(200))
    from_name = db.Column(db.String(200))
    reply_to = db.Column(db.String(200))
    recipients = db.Column(db.Integer)
    created = db.Column(db.DateTime)

    def __init__(self):
        self.created = datetime.datetime.now()
