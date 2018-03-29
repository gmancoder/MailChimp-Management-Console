#!/usr/bin/env python
from models.shared import db
from models.users import *
import core as f
import forms
import json
import datetime
import folders
import unidecode
from sqlalchemy import *
from sqlalchemy import func

def all_users():
	return User.query.all()

def user_by_id(user_id):
    return User.query.get(user_id)

def delete_user(user_id):
    user = user_by_id(user_id)
    if not user:
        return False, "User %s not found" % user_id

    try:
        db.session.delete(user)
        db.session.commit()
        return True, ""
    except Exception as ex:
        return False, str(ex)