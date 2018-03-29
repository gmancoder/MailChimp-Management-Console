#!/usr/bin/env python
from models.shared import db
import datetime

class TrackedCampaign(db.Model):
    __tablename__ = "tracking"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    type = db.Column(db.String(50), default="campaigns")
    campaign_id = db.Column(db.Integer, nullable=False)
    campaign_name = db.Column(db.String(200))
    email_id = db.Column(db.Integer)
    email_name = db.Column(db.String(200))
    list_name = db.Column(db.String(200))
    segment_name = db.Column(db.String(200))
    send_time = db.Column(db.TIMESTAMP, nullable=True)
    subject_line = db.Column(db.String(200))
    from_name = db.Column(db.String(200))
    reply_to = db.Column(db.String(200))

    # Tracking Counts
    # Sent/Delivered
    number_sent = db.Column(db.Integer, default=0)
    number_delivered = db.Column(db.Integer, default=0)
    delivery_rate = db.Column(db.Float, default=0)

    # Bounces
    number_hard_bounces = db.Column(db.Integer, default=0)
    percent_hard_bounces = db.Column(db.Float, default=0)
    number_soft_bounces = db.Column(db.Integer, default=0)
    percent_soft_bounces = db.Column(db.Float, default=0)

    # Opens
    number_opens = db.Column(db.Integer, default=0)
    percent_opens = db.Column(db.Float, default=0)
    number_unique_opens = db.Column(db.Integer, default=0)
    
    # Clicks
    number_clicks = db.Column(db.Integer, default=0)
    percent_clicks = db.Column(db.Float, default=0)
    number_unique_clicks = db.Column(db.Integer, default=0)
    
    # Unsub
    number_unsubs = db.Column(db.Integer, default=0)

    # ECommerce
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0)
    total_revenue = db.Column(db.Float, default=0)

    # Variate
    variate_campaign_winner_criteria = db.Column(db.String(10), default="opens")
    variate_campaign_wait_time = db.Column(db.Integer, default=60)
    variate_campaign_test_size = db.Column(db.Integer, default=10)
    variate_campaign_test_type = db.Column(db.String, default="subject_line")
    variate_campaign_test_combinations = db.Column(db.Integer, default=2)
    variate_campaign_details = db.relationship("TrackedCampaignVariateDetail", lazy="dynamic", cascade="all,delete")

    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()

class TrackedCampaignVariateDetail(db.Model):
    __tablename__ = "tracking_variate_detail"
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.Integer, db.ForeignKey("tracking.id"))
    email_name = db.Column(db.String(200))
    email_id = db.Column(db.Integer, db.ForeignKey("email.id"))
    send_time = db.Column(db.TIMESTAMP, nullable=True)
    subject_line = db.Column(db.String(200))
    from_name = db.Column(db.String(200))
    reply_to = db.Column(db.String(200))
    recipients = db.Column(db.Integer)
    is_winner = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime)

    def __init__(self):
        self.created = datetime.datetime.now()

class TrackingExportDefinition(db.Model):
    __tablename__ = "tracking_export_definition"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    name = db.Column(db.String(200))
    file_path = db.Column(db.String(1024))
    file_delimiter = db.Column(db.String(1), default=",")
    target_id = db.Column(db.Integer, db.ForeignKey("tracking.id"))
    target_activity = db.Column(db.String(20))
    target_type = db.Column(db.String(20), nullable=True)
    system_definition = db.Column(db.Boolean, default=False)
    notify_addresses = db.Column(db.String(1024), nullable=True)
    activity = db.relationship("TrackingExportActivity", lazy="dynamic")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class TrackingExportActivity(db.Model):
    __tablename__ = "tracking_export_actvity"
    id = db.Column(db.Integer, primary_key=True)
    tracking_export_definition_id = db.Column(db.Integer, db.ForeignKey("tracking_export_definition.id"))
    start_date = db.Column(db.TIMESTAMP, nullable=True)
    end_date = db.Column(db.TIMESTAMP, nullable=True)
    status = db.Column(db.Integer, default=0)
    total_rows = db.Column(db.Integer, default=0)
    errors = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()