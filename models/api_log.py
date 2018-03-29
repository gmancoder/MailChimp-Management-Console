#!/usr/bin/env python
from models.shared import db
import datetime

class APILog(db.Model):
    __tablename__ = "api_log"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200))
    method = db.Column(db.String(200))
    request_fields = db.relationship("APIRequestField", lazy="dynamic")
    status = db.Column(db.Boolean, nullable=True)
    status_type = db.Column(db.String(50), nullable=True)
    response = db.Column(db.String(4000), nullable=True)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.Integer)

    def __init__(self):
        self.created = datetime.datetime.now()

class APIRequestField(db.Model):
    __tablename__ = "api_request_field"
    id = db.Column(db.Integer, primary_key=True)
    api_log_id = db.Column(db.Integer, db.ForeignKey("api_log.id"))
    key = db.Column(db.String(200))
    value = db.Column(db.String(4000))
    created = db.Column(db.DateTime)

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.created = datetime.datetime.now()
