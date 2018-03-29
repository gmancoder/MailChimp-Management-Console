#!/usr/bin/env python
from models.shared import db
from models.brands import *
import core as f
import forms
import json
import datetime
import folders
import unidecode
from sqlalchemy import *
from sqlalchemy import func

def all_brands():
	return Brand.query.order_by(Brand.client).all()

def brand_by_id(brand_id):
    return Brand.query.get(brand_id)

