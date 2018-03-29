#!/usr/bin/env python
from models.shared import db
import datetime

class DataView_Open(db.Model):
    __tablename__ = "data_view_open"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"))
    email_id = db.Column(db.String(50))
    email_address = db.Column(db.String(200))
    unique_email_id = db.Column(db.String(200))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    event_date = db.Column(db.TIMESTAMP)
    campaign_title = db.Column(db.String(200), nullable=True)

class DataView_Sent(db.Model):
    __tablename__ = "data_view_sent"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"))
    email_id = db.Column(db.String(50))
    email_address = db.Column(db.String(200))
    unique_email_id = db.Column(db.String(200))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    event_date = db.Column(db.TIMESTAMP)
    campaign_title = db.Column(db.String(200), nullable=True)

class DataView_Click(db.Model):
    __tablename__ = "data_view_click"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"))
    email_id = db.Column(db.String(50))
    email_address = db.Column(db.String(200))
    unique_email_id = db.Column(db.String(200))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    event_date = db.Column(db.TIMESTAMP)
    campaign_title = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(200), nullable=True)

class DataView_Bounce(db.Model):
    __tablename__ = "data_view_bounce"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"))
    email_id = db.Column(db.String(50))
    email_address = db.Column(db.String(200))
    unique_email_id = db.Column(db.String(200))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    event_date = db.Column(db.TIMESTAMP)
    campaign_title = db.Column(db.String(200), nullable=True)
    bounce_type = db.Column(db.String(200), nullable=True)

class DataView_Unsubscribe(db.Model):
    __tablename__ = "data_view_unsubscribe"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"))
    email_id = db.Column(db.String(50))
    email_address = db.Column(db.String(200))
    unique_email_id = db.Column(db.String(200))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    event_date = db.Column(db.TIMESTAMP)
    campaign_title = db.Column(db.String(200), nullable=True)
    unsubscribe_type = db.Column(db.String(200), nullable=True)
