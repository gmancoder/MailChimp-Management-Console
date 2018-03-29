#!/usr/bin/env python
from models.shared import db
import datetime

segment_subscribers = db.Table('segment_subscriber',
                      db.Column('segment_id', db.Integer, db.ForeignKey('segment.id')),
                      db.Column('list_subscriber_id', db.Integer, db.ForeignKey('list_subscriber.id'))
                      , extend_existing=True)

class Segment(db.Model):
    __tablename__ = "segment"
    id = db.Column(db.Integer, primary_key=True)
    mailchimp_id = db.Column(db.String(50))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    name = db.Column(db.String(200))
    type = db.Column(db.String(50), default="saved")
    match = db.Column(db.String(3), default="any")
    subscribers = db.relationship('ListSubscriber', secondary=segment_subscribers, lazy='dynamic', cascade="all,delete")
    conditions = db.relationship("SegmentCondition", lazy='dynamic', cascade="all,delete", backref="segment")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class SegmentCondition(db.Model):
    __tablename__ = "segment_condition"
    id = db.Column(db.Integer, primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey("segment.id"))
    type = db.Column(db.String(50))
    op = db.Column(db.String(50))
    field = db.Column(db.String(100))
    value = db.Column(db.String(200))
    created = db.Column(db.DateTime)

    def __init__(self):
        self.created = datetime.datetime.now()
