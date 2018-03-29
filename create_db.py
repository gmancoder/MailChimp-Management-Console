#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mailchimp import app, db
from models.forms import *
import datetime
with app.app_context():
	fields = FormField.query.all()
	for field in fields:
		print 'Updating %s' % field.label
		field.search = False
		if field.name in ("name", 'mailchimp_id'):
			field.search = True
		field.export = True
		field.updated = datetime.datetime.now()
		field.updated_by = 2
		field.created_by = 2
		db.session.commit()
    
