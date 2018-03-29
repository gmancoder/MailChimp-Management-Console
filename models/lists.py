#!/usr/bin/env python
from models.shared import db
import datetime

class List(db.Model):
    __tablename__ = "list"
    id = db.Column(db.Integer, primary_key=True)
    mailchimp_id = db.Column(db.String(50))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    folder = db.relationship("Folder", backref="list")
    name = db.Column(db.String(200))
    contact = db.relationship("ListContact", backref="list", cascade="all,delete")
    campaign_defaults = db.relationship('ListCampaignDefaults', backref="list", cascade="all,delete")
    activity = db.relationship("ListActivity", backref="list", lazy="dynamic", cascade="all,delete")
    subscribers = db.relationship('ListSubscriber', backref='list', lazy='dynamic', cascade="all,delete")
    merge_fields = db.relationship('ListMergeField', lazy="dynamic", cascade="all,delete")
    permission_reminder = db.Column(db.String(1024))
    notify_on_subscribe = db.Column(db.String(200))
    notify_on_unsubscribe = db.Column(db.String(200))
    email_type_option = db.Column(db.Integer, default=1)
    visibility = db.Column(db.String(3), default="pub")
    campaign_last_sent = db.Column(db.TIMESTAMP, nullable=True)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ListContact(db.Model):
    __tablename__ = "list_contact"
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))
    company = db.Column(db.String(200))
    address1 = db.Column(db.String(200))
    address2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(200))
    state = db.Column(db.String(200))
    zip = db.Column(db.String(200))
    country = db.Column(db.String(200))
    phone = db.Column(db.String(200), nullable=True)
    
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ListCampaignDefaults(db.Model):
    __tablename__ = "list_campaign_default"
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))
    from_name = db.Column(db.String(200))
    from_email = db.Column(db.String(200))
    subject = db.Column(db.String(200))
    language = db.Column(db.String(200))
    
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ListMergeField(db.Model):
    __tablename__ = "list_merge_field"
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))
    mailchimp_id = db.Column(db.Integer)
    tag = db.Column(db.String(20))
    name = db.Column(db.String(200))
    type = db.Column(db.String(20))
    required = db.Column(db.Boolean, default=True)
    default_value = db.Column(db.String(200), nullable=True)
    public = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    choices = db.relationship("ListMergeFieldChoice", lazy="dynamic", cascade="all,delete")
    size = db.Column(db.Integer, default=0)
    default_country = db.Column(db.String(5), nullable=True)
    phone_format = db.Column(db.String(50), nullable=True)
    date_format = db.Column(db.String(50), nullable=True)

    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ListMergeFieldChoice(db.Model):
    __tablename__ = "list_merge_field_choice"
    id = db.Column(db.Integer, primary_key=True)
    list_merge_field_id = db.Column(db.Integer, db.ForeignKey("list_merge_field.id"))
    choice = db.Column(db.String(200))
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self, choice = None):
        if choice != None:
            self.choice = choice
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ListActivity(db.Model):
    __tablename__ = "list_activity"
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))
    day = db.Column(db.Date)
    emails_sent = db.Column(db.Integer, default=0)
    unique_opens = db.Column(db.Integer, default=0)
    recipient_clicks = db.Column(db.Integer, default=0)
    hard_bounce = db.Column(db.Integer, default=0)
    soft_bounce = db.Column(db.Integer, default=0)
    subs = db.Column(db.Integer, default=0)
    unsubs = db.Column(db.Integer, default=0)
    other_adds = db.Column(db.Integer, default=0)
    other_removes = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self, choice = None):
        if choice != None:
            self.choice = choice
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()
