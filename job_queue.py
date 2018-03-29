#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mailchimp import app, db
from models.system_jobs import *
from sqlalchemy import *
with app.app_context():
    jobs = SystemJob.query.filter(SystemJob.overall_status == 0).order_by(SystemJob.created.asc()).all()
    for job in jobs:
        status = job.run()
        print status    
