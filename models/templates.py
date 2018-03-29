#!/usr/bin/env python
from models.shared import db
import datetime

class Template(db.Model):
    __tablename__ = "template"
    id = db.Column(db.Integer, primary_key=True)
    mailchimp_id = db.Column(db.String(50))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('template_category.id'), nullable=True)
    folder = db.relationship("Folder", backref="templates")
    category = db.relationship("TemplateCategory", backref="templates")
    name = db.Column(db.String(200))
    type = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)
    thumbnail = db.Column(db.String(1024), nullable=True)
    html = db.Column(db.Text, nullable=False)
    sections = db.relationship("TemplateSection", backref="template", lazy="dynamic")
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class TemplateCategory(db.Model):
    __tablename__ = "template_category"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brand.id"))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    name = db.Column(db.String(200))
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class TemplateSection(db.Model):
    __tablename__ = "template_section"
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("template.id"))
    tag = db.Column(db.String(100))
    default_content = db.Column(db.Text)
