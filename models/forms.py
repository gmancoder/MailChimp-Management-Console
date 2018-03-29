#!/usr/bin/env python
from models.shared import db
import datetime

class FormGroup(db.Model):
    __tablename__ = "form_group"
    id = db.Column(db.Integer, primary_key=True)
    form_type = db.Column(db.String(50))
    name = db.Column(db.String(50))
    rank = db.Column(db.Integer, default=1)
    fields = db.relationship("FormField", backref="form_group", lazy="dynamic", order_by="asc(FormField.rank)")
    fieldset_on_form = db.Column(db.Boolean, default=True)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class FormField(db.Model):
    __tablename__ = "form_field"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('form_group.id'))
    name = db.Column(db.String(100))
    label = db.Column(db.String(100))
    rank = db.Column(db.Integer, default=1)
    required = db.Column(db.Boolean, default=True)
    create = db.Column(db.Boolean, default=True)
    update = db.Column(db.Boolean, default=True)
    search = db.Column(db.Boolean, default=False)
    export = db.Column(db.Boolean, default=True)
    tag = db.Column(db.String(20))
    field_type = db.Column(db.String(20))
    max_length = db.Column(db.Integer, default=1)
    default_value = db.Column(db.String(200), nullable=True)
    options = db.relationship("FormFieldOption", backref="form_field", lazy="dynamic")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class FormFieldOption(db.Model):
    __tablename__ = "form_field_option"
    id = db.Column(db.Integer, primary_key=True)
    form_field_id = db.Column(db.Integer, db.ForeignKey("form_field.id"))
    value = db.Column(db.String(200))
    label = db.Column(db.String(200))
    
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()


