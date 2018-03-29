#!/usr/bin/env python
from models.shared import db
import datetime

class SystemMergeField(db.Model):
    __tablename__ = "system_merge_field"
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50))
    name = db.Column(db.String(200))
    description = db.Column(db.Text, nullable=True)
    created = db.Column(db.DateTime)

    def __init__(self):
        self.created = datetime.datetime.now()
