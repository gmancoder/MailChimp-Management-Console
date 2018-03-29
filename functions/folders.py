#!/usr/bin/env python
from models.shared import db
from models.folders import *
from sqlalchemy import *
import core as f
import lists
import json
import inflection

def create_folder(brand_id, name, parent_id, folder_type):
	mailchimp_id = None
	if folder_type in ('templates', 'campaigns', 'ab_tests'):
		status, new_folder = add_folder_to_mailchimp(brand_id, name, folder_type)
		if not status:
			return False, new_folder

		mc_folder = json.loads(new_folder)
		mailchimp_id = mc_folder['id']
	
	status, new_folder = add_new_folder(brand_id, name, parent_id, folder_type, mailchimp_id)
	if not status:
		return False, new_folder

	return True, new_folder

def add_new_folder(brand, name, parent_id, folder_type, mailchimp_id=None):
	new_folder = Folder(name, parent_id)
	new_folder.folder_type = folder_type
	new_folder.mailchimp_id = mailchimp_id
	new_folder.brand_id = brand
	try:
		db.session.add(new_folder)
		db.session.commit()
		return True, new_folder
	except Exception as e:
		return False, str(e)

def delete_folder(brand, folder_id):
	status, folder = get_folder_by_id(brand, folder_id)
	if status:
		if len(folder.children) > 0:
			return False, "Folder has subfolders"
		elif folder_has_items(folder_id, folder.folder_type):
			return False, "Folder not empty"
		#elif folder.lists and len(folder.lists) > 0:
		#	return False, "Folder not empty"
		try:
			if folder.mailchimp_id != None:
				status, response = delete_mailchimp_folder(brand, folder.folder_type, folder.mailchimp_id)
				if not status:
					return False, response
			db.session.delete(folder)
			db.session.commit()
			return True, ""
		except Exception as e:
			return False, str(e)
	return False, "Folder with ID %s doesn't exist" % folder_id

def rename_folder(brand_id, folder_id, name):
	status, folder = get_folder_by_id(brand_id, folder_id)
	if status:
		folder.name = name
		if folder.mailchimp_id != None:
			status, response = update_mailchimp_folder(brand_id, folder.mailchimp_id, folder.folder_type, name)
			if not status:
				return False, response
		try:
			db.session.commit()
			return True, folder
		except Exception as e:
			return False, str(e)
	return False, "Folder not found"

def get_folders(brand, folder_id=None, folder_type=None):
	if folder_id != None:
		status, folder = get_folder_by_id(brand, folder_id)
		if status:
			return True, f._obj_to_dict([folder])
		else:
			return False, "Folder Not Found"
	elif folder_type != None:
		folders = Folder.query.filter(and_(Folder.folder_type == folder_type, Folder.brand_id == brand)).all()
		if folders and len(folders) > 0:
			return True, f._obj_to_dict(folders)
		else:
			return False, "No Folders Found"
	else:
		folders = Folder.query.filter(Folder.brand_id == brand).all()
		if folders and len(folders) > 0:
			return True, f._obj_to_dict(folders)
		else:
			return False, "No Folders Found"

def get_folder_by_id(brand_id, folder_id):
	g_folder = Folder.query.filter(and_(Folder.brand_id == brand_id, Folder.id == folder_id)).first()
	if not g_folder:
		return False, "Folder not found"
	return True, g_folder
def get_root_folder(brand, folder_type):
	folder = Folder.query.filter(and_(Folder.folder_type == folder_type, Folder.brand_id == brand, Folder.parent_folder_id == None)).first()
	if folder:
		return folder
	return create_root_folder(brand, folder_type)

def create_root_folder(brand, folder_type):
	status, new_folder = create_folder(brand, folder_type.title(), None, folder_type)
	if status:
		return new_folder
	print new_folder
	return None

def add_folder_to_mailchimp(brand_id, name, folder_type):
	brand = f.GetBrandByID(brand_id)
	data = {'name': name}
	if folder_type == "templates":
		data_type = "template-folders"
	elif folder_type in ("campaigns", 'ab_tests'):
		data_type = "campaign-folders"
	else:
		return False, "Mailchimp doesn't have folders of type '%s'" % folder_type

	return f.post_to_mailchimp(brand, data_type, json.dumps(data))

def update_mailchimp_folder(brand_id, mailchimp_id, folder_type, name):
	brand = f.GetBrandByID(brand_id)
	data = {'name': name}
	if folder_type == "templates":
		data_type = "template-folders"
	elif folder_type in ("campaigns", 'ab_tests'):
		data_type = "campaign-folders"
	else:
		return False, "Mailchimp doesn't have folders of type '%s'" % folder_type

	return f.patch_to_mailchimp(brand, data_type, json.dumps(data), mailchimp_id)

def delete_mailchimp_folder(brand_id, folder_type, mailchimp_id):
	brand = f.GetBrandByID(brand_id)
	if folder_type == "templates":
		data_type = "template-folders"
	elif folder_type == "campaigns":
		data_type = "campaign-folders"
	else:
		return False, "Mailchimp doesn't have folders of type '%s'" % folder_type

	return f.delete_to_mailchimp(brand, data_type, mailchimp_id)

def folder_has_items(folder_id, folder_type):
	sql = "select count(*) from %s where folder_id = %s" % (inflection.singularize(folder_type), folder_id)
	try:
		result = db.engine.execute(sql)
		for row in result:
			if int(row[0]) > 0:
				return True
		return False
	except Exception as ex:
		print ex
		return True