#!/usr/bin/env python
from models.shared import db
from models.brands import brand_tools
import datetime

class ToolGroup(db.Model):
    __tablename__ = 'tool_group'
    __table_args__ = {'useexisting': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    alias = db.Column(db.String(200))
    rank = db.Column(db.Integer)
    icon = db.Column(db.String(100))
    tools = db.relationship('Tool', backref='tool_group', lazy='dynamic', cascade="all,delete")
    status = db.Column(db.Integer, default=1)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self, name=None, alias=None):
        self.name = name
        self.alias = alias
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class Tool(db.Model):
    __tablename__ = "tool"
    __table_args__ = {'useexisting': True}
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("tool_group.id"))
    name = db.Column(db.String(200))
    description = db.Column(db.String(200))
    alias = db.Column(db.String(200))
    home_route = db.Column(db.String(200))
    rank = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Integer, default=0)
    settings = db.relationship("ToolSetting", backref="tool", lazy='dynamic', cascade="all,delete")
    group = db.relationship("ToolGroup", backref="tool")
    brands = db.relationship('Brand', secondary=brand_tools, lazy='dynamic')
    status = db.Column(db.Integer, default=1)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self, name=None, alias=None):
        self.name = name
        self.alias = alias
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ToolSetting(db.Model):
    __tablename__ = "tool_setting"
    __table_args__ = {'useexisting': True}
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey("tool.id"))
    key = db.Column(db.String(200))
    value = db.Column(db.String(200))
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()
