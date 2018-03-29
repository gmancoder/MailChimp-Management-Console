#!/usr/bin/env python
from models.shared import db
import datetime

class FileLocation(db.Model):
    __tablename__ = "file_location"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer)
    name = db.Column(db.String(200))
    type = db.Column(db.String(50), default="internal")
    internal_location = db.Column(db.String(10), default="imports")
    external_host = db.Column(db.String(50), nullable=True)
    external_port = db.Column(db.Integer, default=21)
    external_user = db.Column(db.String(50), nullable=True)
    external_pass = db.Column(db.String(50), nullable=True)
    external_path = db.Column(db.String(2000), nullable=True)

    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()