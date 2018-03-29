#!/usr/bin/env python
from models.shared import db

def AddLog(log):
    db.session.add(log)
    db.session.commit()
