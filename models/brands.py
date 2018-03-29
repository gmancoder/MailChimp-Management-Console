#!/usr/bin/env python
from models.shared import db
import datetime

brand_tools = db.Table('brand_tool',
                      db.Column('brand_id', db.Integer, db.ForeignKey('brand.id')),
                      db.Column('tool_id', db.Integer, db.ForeignKey('tool.id'))
                      , extend_existing=True)

class Brand(db.Model):
    __tablename__ = 'brand'
    __table_args__ = {'useexisting': True}
    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.String(100))
    mid = db.Column(db.Integer)
    api_user = db.Column(db.String(50))
    api_key = db.Column(db.String(50))
    api_dc = db.Column(db.String(10))
    tools = db.relationship('Tool', secondary=brand_tools, lazy='dynamic')
    status = db.Column(db.Integer, default=1)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()