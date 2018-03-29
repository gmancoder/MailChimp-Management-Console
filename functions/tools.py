#!/usr/bin/env python
from models.shared import db
from models.tools import *
from sqlalchemy import *
import core as f
import json
import datetime
import inflection

def write_template(in_path, out_path, name, alias, append=False):
    ifh = open(in_path, 'r')
    if append:
        ofh = open(out_path, 'a')
    else:
        ofh = open(out_path, 'w')
    for line in ifh.readlines():
        line = line.replace('TOOL_NAME_SINGLE', inflection.singularize(name).title())
        line = line.replace('TOOL_NAME', name.title())
        line = line.replace('TOOL_ALIAS_SINGLE', inflection.singularize(alias))
        line = line.replace('TOOL_ALIAS', alias)
        ofh.write('%s' % line)
    ofh.close()
    ifh.close()

def touch_file(in_file):
    fh = open(in_file, 'w')
    fh.close()

def tool_group_by_id(tool_group_id):
    return ToolGroup.query.get(tool_group_id)

def tool_by_alias(alias):
    return Tool.query.filter(Tool.alias == alias).first()

def get_settings(tool_id, for_table=False):
    settings = ToolSetting.query.filter(ToolSetting.tool_id == tool_id).all()
    if for_table:
        setting_list = []
        for setting in settings:
            setting_dict = {'id': setting.id, 'key': setting.key, 'value': setting.value, 'updated': str(setting.updated)}
            setting_list.append(setting_dict)
        return setting_list
    return settings

def add_setting(tool_id, key, value, user):
    if ToolSetting.query.filter_by(key=key,tool_id=tool_id).count() == 0:
        new_setting = ToolSetting(key, value)
        new_setting.tool_id = tool_id
        new_setting.created_by = user.username
        new_setting.updated_by = user.username

        db.session.add(new_setting)
        db.session.commit()
        
        return True, get_settings(tool_id, True)
    else:
        msg='Setting with key "%s" already exists' % key
        return False, msg

def delete_setting(id):
    setting = ToolSetting.query.get(id)
    if not setting:
        return False, "Setting not found"
    try:
        db.session.delete(setting)
        db.session.commit()

        return True, ""
    except Exception as ex:
        return False, str(ex)
