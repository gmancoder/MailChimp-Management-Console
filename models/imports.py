#!/usr/bin/env python
from models.shared import db
import datetime

class ImportDefinition(db.Model):
    __tablename__ = "import_definition"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    name = db.Column(db.String(200))
    file_path = db.Column(db.String(1024))
    file_delimiter = db.Column(db.String(1), default=",")
    target_type = db.Column(db.String(200))
    target_folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"), nullable=True)
    target_list_id = db.Column(db.Integer, db.ForeignKey("list.id"), nullable=True)
    import_type = db.Column(db.Integer, default=1) # 1 = Add/Update, 2 = Add Only, 3 = Update Only
    system_definition = db.Column(db.Boolean, default=False)
    notify_addresses = db.Column(db.String(1024), nullable=True)
    mappings = db.relationship("ImportFieldMapping", backref="import_definition", lazy="dynamic")
    activity = db.relationship("ImportActivity", lazy="dynamic")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ImportFieldMapping(db.Model):
    __tablename__ = "import_field_mapping"
    id = db.Column(db.Integer, primary_key=True)
    import_definition_id = db.Column(db.Integer, db.ForeignKey("import_definition.id"))
    source_field = db.Column(db.String(100))
    destination_field = db.Column(db.String(100))
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class ImportActivity(db.Model):
    __tablename__ = "import_actvity"
    id = db.Column(db.Integer, primary_key=True)
    import_definition_id = db.Column(db.Integer, db.ForeignKey("import_definition.id"))
    start_date = db.Column(db.TIMESTAMP, nullable=True)
    end_date = db.Column(db.TIMESTAMP, nullable=True)
    status = db.Column(db.Integer, default=0)
    total_rows = db.Column(db.Integer, default=0)
    inserts = db.Column(db.Integer, default=0)
    updates = db.Column(db.Integer, default=0)
    ignored = db.Column(db.Integer, default=0)
    errors = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()
