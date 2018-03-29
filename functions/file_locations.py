#!/usr/bin/env python
from models.shared import db
from models.file_locations import *
import core as f
import json
import datetime
import unidecode
import base64
from sqlalchemy import *
from sqlalchemy import func

def file_location_by_name(brand_id, name, count=False):
    query = FileLocation.query.filter(and_(FileLocation.brand_id == brand_id, FileLocation.name == name))
    if count:
        return query.count()
    else:
        return query.all()

def request_to_file_location(file_location, request):
    file_location.brand_id = int(request['brand'])
    
    if file_location.name != request['name'] and file_location_by_name(file_location.brand_id, request['name'], True) > 0:
        return False, "File Location '%s' already exists" % request['name'], file_location
    file_location.name = request['name']
    
    file_location.type = request['type']
    if file_location.type == 'internal':
        file_location.internal_location = request['internal_location']
    else:
        if request['external_host'] == "" or request['external_user'] == "" or request['external_pass'] == "" or request['external_path'] == "":
            return False, "External Properties Missing", file_location
        else:
            file_location.external_host = request['external_host']
            file_location.external_user = request['external_user']
            file_location.external_pass = base64.b64encode(request['external_pass'])
            file_location.external_path = request['external_path']
    return True, "", file_location

def save_file_location(mode, file_location, user):
    try:
        if mode == "new":
            file_location.created_by = user.id
            db.session.add(file_location)
        file_location.updated_by = user.id
        file_location.updated = datetime.datetime.now()
        db.session.commit()
        return True, "File Location saved"
    except Exception as ex:
        return False, "File Location NOT saved - %s" % str(ex)

def delete_file_location(id):
    file_location = FileLocation.query.get(id)
    if not file_location:
        return False, "File Location not found"

    try:
        db.session.delete(file_location)
        db.session.commit()
        return True, ""
    except Exception as ex:
        return False, str(ex)