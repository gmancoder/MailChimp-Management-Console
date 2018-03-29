#!/usr/bin/env python
from models.shared import db
import datetime

class Email(db.Model):
    __tablename__ = "email"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    folder_id = db.Column(db.Integer, db.ForeignKey("folder.id"))
    template_id = db.Column(db.Integer, db.ForeignKey("template.id"))
    name = db.Column(db.String(200))
    subject = db.Column(db.String(100))
    sections = db.relationship("EmailSection", backref="email", lazy="dynamic", cascade="all,delete")
    last_sent = db.Column(db.TIMESTAMP, nullable=True)
    full_html = db.Column(db.Text, nullable=True)
    html_by = db.Column(db.String(50))
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

class EmailSection(db.Model):
    __tablename__ = "email_section"
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey("email.id"))
    tag = db.Column(db.String(100))
    content = db.Column(db.Text)
