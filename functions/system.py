#!/usr/bin/env python
from models.shared import db
from models.system_merge_fields import *
from sqlalchemy import *
import core as f
import json
import datetime

def system_merge_field():
	fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'Name', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'tag': {'Label': 'Tag', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 50,
        'Rank': 2,
        }},
    'description': {'Label': 'Description', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'textarea',
        'Type': 'textarea',
        'Rank': 3,
        }}
    }

def system_merge_field_to_db(name, tag, description, user, id=None):
	if id == None:
		return add_system_merge_field_to_db(name, tag, description, user)
	else:
		return update_system_merge_field_to_db(id, name, tag, description, user)

def system_merge_field_fields_to_object(system_merge_field, name, tag, description):
	system_merge_field.name = name
	system_merge_field.tag = tag
	system_merge_field.description = description
	return system_merge_field

def add_system_merge_field_to_db(name, tag, description, user):
	system_merge_field = SystemMergeField()
	system_merge_field = system_merge_field_fields_to_object(system_merge_field, name, tag, description)
	system_merge_field.created_by = user.id

	try:
		db.session.add(system_merge_field)
		db.session.commit()
		return True, f._obj_to_dict([system_merge_field])
	except Exception as ex:
		return False, str(ex)

def update_system_merge_field_to_db(id, name, tag, description, user):
	system_merge_field = SystemMergeField.query.get(id)
	if not system_merge_field:
		return False, "System Merge Field not found"

	system_merge_field = system_merge_field_fields_to_object(system_merge_field, name, tag, description)
	system_merge_field.updated_by = user.id
	system_merge_field.updated = datetime.datetime.now()

	try:
		db.session.commit()
		return True, f._obj_to_dict([system_merge_field])
	except Exception as ex:
		return False, str(ex)
	
def get_all_system_merge_fields():
	return SystemMergeField.query.order_by(SystemMergeField.name.asc()).all()

def get_all_system_merge_fields_dict():
	system_merge_fields = get_all_system_merge_fields()
	return f._obj_to_dict(system_merge_fields)