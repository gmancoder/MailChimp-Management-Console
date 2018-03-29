#!/usr/bin/env python
from models.shared import db
from flask_login import AnonymousUserMixin
import datetime
import uuid

user_brands = db.Table('user_brand',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('brand_id', db.Integer, db.ForeignKey('brand.id')))

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(25), unique=True)
    password = db.Column(db.String(36))
    brands = db.relationship('Brand', secondary=user_brands, backref=db.backref("users", lazy='dynamic'), lazy='dynamic')
    status = db.Column(db.Integer, default=1)
    admin = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime)
    updated = db.Column(db.DateTime)

    def __init__(self, name=None, email=None, username=None, passwd=None):
        self.name = name
        self.email = email
        self.username = username
        self.password = passwd
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

    def __repr__(self):
        return '<User %r>' % (self.name)

    def is_authenticated(self):
        return not type(self) is AnonymousUserMixin

    def is_active(self):
        return self.status == 1

    def is_admin(self):
        return self.admin == 1

    def is_anonymous(self):
        return type(self) is AnonymousUserMixin

    def get_id(self):
        return unicode(self.id)


class UserSession(db.Model):
    __tablename__ = "user_session"
    __table_args__ = {'useexisting': True}
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created = db.Column(db.DateTime)
    last_used = db.Column(db.DateTime)

    def __init__(self, user=None):
        self.token = str(uuid.uuid4())
        self.user_id = user
        self.created = datetime.datetime.now()

