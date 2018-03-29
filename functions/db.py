#!/usr/bin/env python
from models.shared import db
import uuid
import re
from flask import g

def GetData(table_name, fields, order = None):
    try:
        tbl = db.Table(table_name, db.metadata)
        #flds = ','.join(fields)
        data = db.engine.connect().execute(tbl.select(order_by=order, bind=db.engine))
        items = []
        for d in data:
            item = {}
            for x in range(0, len(fields)):
                item[fields[x]] = d[x]
            items.append(item)
        #print 'Table Select'
        return True, items, ""
    except Exception as e:
        return False, [], str(e)

def _execute(sql):
    db.session.execute(sql)
    db.session.commit()
