#!/usr/bin/env python
from models.shared import db
import datetime

class ListSubscriber(db.Model):
    __tablename__ = "list_subscriber"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))
    email_id = db.Column(db.String(50))
    email_address = db.Column(db.String(200))
    unique_email_id = db.Column(db.String(200))
    email_type = db.Column(db.String(10), default="html")
    status = db.Column(db.String(20))
    location = db.relationship("ListSubscriberLocation", lazy="dynamic", cascade="delete")
    merge_fields = db.relationship('ListSubscriberMergeField', backref='list_subscriber', lazy='dynamic', cascade="delete")
    activity = db.relationship("ListSubscriberActivity", backref="list_subscriber", lazy="dynamic", cascade="delete")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ListSubscriberLocation(db.Model):
    __tablename__ = "list_subscriber_location"
    id = db.Column(db.Integer, primary_key=True)
    list_subscriber_id = db.Column(db.Integer, db.ForeignKey('list_subscriber.id'))
    latitude = db.Column(db.String(200), nullable=True)
    longitude = db.Column(db.String(200), nullable=True)
    gmtoff = db.Column(db.String(200), nullable=True)
    dstoff = db.Column(db.String(200), nullable=True)
    country_code = db.Column(db.String(200), nullable=True)
    timezone = db.Column(db.String(200), nullable=True)
    created = db.Column(db.DateTime)

    def __init__(self):
        self.created = datetime.datetime.now()

class ListSubscriberMergeField(db.Model):
    __tablename__ = "list_subscriber_merge_field"
    id = db.Column(db.Integer, primary_key=True)
    list_subscriber_id = db.Column(db.Integer, db.ForeignKey('list_subscriber.id'))
    list_merge_field_id = db.Column(db.Integer, db.ForeignKey('list_merge_field.id', ondelete='CASCADE'))
    value = db.Column(db.String(200))
    
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ListSubscriberActivity(db.Model):
    __tablename__ = "list_subscriber_activity"
    id = db.Column(db.Integer, primary_key=True)
    list_subscriber_id = db.Column(db.Integer, db.ForeignKey('list_subscriber.id'))
    action = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=True)
    url = db.Column(db.String(200), nullable=True)
    type = db.Column(db.String(200), nullable=True)
    variate_campaign_id = db.Column(db.Integer, db.ForeignKey("variate_campaign.id"))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"))
    title = db.Column(db.String(200), nullable=True)
    #parent_campaign = db.Column(db.String(20))

    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
