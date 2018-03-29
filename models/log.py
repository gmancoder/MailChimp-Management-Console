#!/usr/bin/env python
from models.shared import db
import datetime

class Log(db.Model):
    __tablename__ = "process_log"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brand.id"))
    brand = db.relationship("Brand", backref="logs")
    tool_id = db.Column(db.Integer, db.ForeignKey("tool.id"))
    tool = db.relationship("Tool", backref="logs")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="logs")
    request_route = db.Column(db.String(150))
    crud_operation = db.Column(db.String(20))
    esp_interaction = db.Column(db.Integer, default=0)
    esp_object = db.Column(db.String(150))
    esp_object_key = db.Column(db.String(40))
    esp_object_name = db.Column(db.String(200))
    esp_operation = db.Column(db.String(50))
    esp_data = db.Column(db.String(2000))
    esp_response = db.Column(db.String(10))
    esp_response_msg = db.Column(db.String(2000))
    rows_affected = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, brand_id, tool_id, user_id, route, op=None, e_int=0, e_obj=None,
                    e_obj_key=None, e_obj_name=None, e_op=None,
                    e_data = None, e_resp=None, e_resp_msg=None, rows=0):
        self.brand_id = brand_id
        self.tool_id = tool_id
        self.user_id = user_id
        self.request_route = route
        self.crud_operation = op
        self.esp_interaction = e_int
        self.esp_object = e_obj
        self.esp_object_key = e_obj_key
        self.esp_object_name = e_obj_name
        self.esp_operation = e_op
        self.esp_data = e_data
        self.esp_response = e_resp
        self.esp_response_msg = e_resp_msg
        self.rows_affected = rows
