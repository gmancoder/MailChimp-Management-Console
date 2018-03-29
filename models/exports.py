#!/usr/bin/env python
from models.shared import db
import datetime

class ExportDefinition(db.Model):
    __tablename__ = "export_definition"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    name = db.Column(db.String(200))
    file_path = db.Column(db.String(1024))
    file_delimiter = db.Column(db.String(1), default=",")
    target_type = db.Column(db.String(200))
    target_folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"), nullable=True)
    target_list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=True)
    target_segment_id = db.Column(db.Integer, db.ForeignKey("segment.id"), nullable=True)
    target_objects = db.relationship("ExportObject", lazy="dynamic")
    export_type = db.Column(db.Integer, default=1)
    system_definition = db.Column(db.Boolean, default=False)
    notify_addresses = db.Column(db.String(1024), nullable=True)
    fields = db.relationship("ExportField", lazy="dynamic")
    activity = db.relationship("ExportActivity", lazy="dynamic")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ExportObject(db.Model):
    __tablename__ = "export_object"
    id = db.Column(db.Integer, primary_key=True)
    export_definition_id = db.Column(db.Integer, db.ForeignKey("export_definition.id"))
    object_id = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ExportField(db.Model):
    __tablename__ = "export_field"
    id = db.Column(db.Integer, primary_key=True)
    export_definition_id = db.Column(db.Integer, db.ForeignKey("export_definition.id"))
    field_name = db.Column(db.String(200))
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ExportActivity(db.Model):
    __tablename__ = "export_actvity"
    id = db.Column(db.Integer, primary_key=True)
    export_definition_id = db.Column(db.Integer, db.ForeignKey("export_definition.id"))
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
