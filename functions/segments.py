import re
import unidecode
from models.shared import db
from models.segments import *
from models.lists import *
from models.list_subscribers import *
import datetime
from flask import redirect, url_for, g, request, flash, session
from flask_login import current_user
import ajax
import db as dbf
import lists
import folders
import core as f
import xml.sax.saxutils as sax
import json
from sqlalchemy import *
import pycountry

def segment():
    fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'Segment Name', 'Required': True, 'Form': {
        'Group': {'Name': 'Segment Details', 'Rank': 1},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1
        }},
    'list_id': {'Label': 'List Name', 'Required': True, 'Form': {
        'Group': {'Name': 'Segment Details', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 2
        }},
    'type': {'Label': 'Segment Type', 'Required': True, 'Form': {
        'Group': {'Name': 'Segment Details', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {'saved': 'Auto', 'static': 'Static'},
        'Rank': 3
        }},
    'match': {'Label': 'Match On', 'Required': True, 'Form': {
        'Group': {'Name': 'Segment Details', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {'any': 'Any', 'all': 'All'},
        'Rank': 4
        }}
    }

    return fields

def all_segments(brand_id, list_id):
    all_segments = Segment.query.filter(and_(Segment.brand_id == brand_id, Segment.list_id == list_id)).all()
    return f._obj_to_dict(all_segments)

def segment_to_form_dict(segment):
    segment_dict = {}
    segment_dict['segments_name'] = segment.name
    segment_dict['segments_list_id'] = segment.list_id
    segment_dict['segments_type'] = segment.type
    segment_dict['segments_match'] = segment.match
    return segment_dict

def segment_by_id(brand_id, segment_id):
    segment = Segment.query.filter(and_(Segment.brand_id == brand_id, Segment.id == segment_id)).first()
    if not segment:
        return False, "Segment not found"
    return True, segment

def segment_by_mailchimp_id(brand_id, segment_id):
    segment = Segment.query.filter(and_(Segment.brand_id == brand_id, Segment.mailchimp_id == segment_id)).first()
    if not segment:
        return False, "Segment not found"
    return True, segment

def segment_to_db(brand_id, folder_id, mailchimp_id, name, type, match, user, conditions=[], list_id=None, list_mailchimp_id=None, id=None):
    if list_id == None and list_mailchimp_id == None:
        return False, "List ID or List Mailchimp ID must be specified"

    if list_id == None:
        current_list = lists.list_by_mailchimp_id(brand_id, list_mailchimp_id)
        if not current_list:
            return False, "List not found by mailchimp id"
        list_id = current_list.id

    if id == None:
        return add_segment_to_db(brand_id, folder_id, list_id, mailchimp_id, name, type, match, user, conditions)
    else:
        return update_segment_to_db(id, brand_id, folder_id, list_id, mailchimp_id, name, type, match, user, conditions)

def add_segment_to_db(brand_id, folder_id, list_id, mailchimp_id, name, type, match, user, conditions=[]):
    segment = Segment()
    segment = segment_fields_to_obj(segment, brand_id, folder_id, list_id, mailchimp_id, name, type, match)
    segment.created_by = user.id

    try:
        db.session.add(segment)
        db.session.commit()
        if len(conditions) > 0:
            status, response = add_conditions_to_segment(segment.id, conditions)
            if not status:
                return False, response
        return True, [segment.__dict__]
    except Exception as ex:
        return False, str(ex)

def segment_fields_to_obj(segment, brand_id, folder_id, list_id, mailchimp_id, name, type, match):
    segment.brand_id = brand_id
    segment.folder_id = folder_id
    segment.list_id = list_id
    segment.mailchimp_id = mailchimp_id
    segment.name = name
    segment.type = type
    segment.match = match

    return segment

def update_segment_to_db(id, brand_id, folder_id, list_id, mailchimp_id, name, type, match, user, conditions=[]):
    status, segment = segment_by_id(brand_id, id)
    if not status:
        return False, segment

    segment = segment_fields_to_obj(segment, brand_id, folder_id, list_id, mailchimp_id, name, type, match)
    segment.updated = datetime.datetime.now()
    segment.updated_by = user.id
    try:
        db.session.commit()
        for condition in segment.conditions.all():
            try:
                db.session.delete(condition)
                db.session.commit()
            except Exception as ex:
                return False, str(ex)

        if len(conditions) > 0:
            status, response = add_conditions_to_segment(segment.id, conditions)
            if not status:
                return False, response
        return True, [segment.__dict__]
    except Exception as ex:
        return False, str(ex)


def add_conditions_to_segment(segment_id, conditions):
    for condition in conditions:
        status, response = add_condition_to_segment(segment_id, condition)
        if not status:
            return False, response
    return True, "OK"

def add_condition_to_segment(segment_id, condition):
    segment_condition = SegmentCondition()
    segment_condition.segment_id = segment_id
    if isinstance(condition, dict):
        segment_condition.type = condition['condition_type']
        segment_condition.op = condition['op']
        segment_condition.field = condition['field']
        segment_condition.value = condition['value']
    else:
        segment_condition.type = condition.type
        segment_condition.op = condition.op
        segment_condition.field = condition.field
        segment_condition.value = condition.value

    try:
        db.session.add(segment_condition)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def segment_to_mailchimp(brand_id, list_id, name, match, conditions=[], static_segment_subscribers=[], mailchimp_id=None):
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Brand not found"
    current_list = lists.list_by_id(brand_id, list_id)
    if not current_list:
        return False, "List Not Found"

    data = {'name': name}
    if len(conditions) > 0:
        data['options'] = {'match': match, 'conditions': []}
        for condition in conditions:
            data['options']['conditions'].append({'condition_type': condition.type, 'field': condition.field, 'op': condition.op, 'value': condition.value})
    elif len(static_segment_subscribers) > 0:
        data['static_segment'] = static_segment_subscribers

    data_str = json.dumps(data)
    #print data_str
    #return False, "TEST"

    if mailchimp_id == None:
        return f.post_to_mailchimp(brand, data_str=data_str, data_type="lists/%s/segments" % current_list.mailchimp_id)
    else:
        return f.patch_to_mailchimp(brand, data_str=data_str, data_type="lists/%s/segments" % current_list.mailchimp_id, id=mailchimp_id)

def segment_condition_from_string(condition_str):
    condition_parts = condition_str.split('|')
    type = condition_parts[0]
    field = condition_parts[1]
    op = condition_parts[2]
    value = condition_parts[3]

    condition = SegmentCondition()
    condition.type = type
    condition.field = field
    condition.op = op
    condition.value = value

    return condition

def move_segment(brand_id, segment_id, folder_id):
    status, current_segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, current_segment

    current_segment.folder_id = folder_id
    try:
        db.session.commit()
        return True, current_segment
    except Exception as ex:
        return False, str(ex)

def search(brand, search_type, search_for, search_contains, search_folder_id):
    fields = ['ID', 'MailChimp ID', 'Name', 'Folder']
    
    query = Segment.query
    if search_type == '1':
        if search_for == 'name':    
            query = query.filter(and_(Segment.brand_id == brand, Segment.name.like('%%%s%%' % search_contains)))
        elif search_for == 'type':
            query = query.filter(and_(Segment.brand_id == brand, Segment.type.like('%%%s%%' % search_contains)))
    elif search_type == '2':
        if search_for == 'name':    
            query = query.filter(and_(Segment.brand_id == brand, Segment.name.like('%%%s%%' % search_contains), Segment.folder_id == folder_id))
        elif search_for == 'type':
            query = query.filter(and_(Segment.brand_id == brand, Segment.type.like('%%%s%%' % search_contains), Segment.folder_id == folder_id))
    segments = query.order_by(Segment.name.asc()).all()
    rows = []
    for segment in segments:
        status, flds = folders.get_folders(brand, folder_id=segment.folder_id)
        if not status:
            return False, flds
        row = {}
        row['ID'] = segment.id
        row['MailChimp ID'] = segment.mailchimp_id
        row['Name'] = "<a href='/segments/%s/detail'>%s</a>" % (segment.id, segment.name)
        row['Folder'] = flds[0]['name']
        rows.append(row)
    return True, {'Fields': fields, 'Data': rows}

def delete_segment(brand_id, segment_id):
    status, segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, segment
    current_list = lists.list_by_id(brand_id, segment.list_id)
    if not current_list:
        return False, "List Not Found"
    try:
        status, response = delete_mailchimp_segment(brand_id, segment.mailchimp_id, current_list.mailchimp_id)
        if not status:
            return False, res
        db.session.delete(segment)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)
    
def delete_mailchimp_segment(brand_id, segment_id, list_id):
    brand = f.GetBrandByID(brand_id)
    return f.delete_to_mailchimp(brand, data_type="lists/%s/segments" % list_id, id=segment_id)

def apply_segment_subscribers_from_mailchimp(brand_id, segment_id):
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Brand not found"
    status, segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, segment
    current_list = lists.list_by_id(brand_id, segment.list_id)
    if not current_list:
        return False, "List Not Found"

    for subscriber in segment.subscribers.all():
        segment.subscribers.remove(subscriber)
    #db.session.flush()
    db.session.commit()

    status, response = f.post_to_mailchimp(brand, data_type='lists/%s/segments/%s/members' % (current_list.mailchimp_id, segment.mailchimp_id), method="GET")
    if not status:
        return False, response

    j_response = json.loads(response)
    members = j_response['members']
    ids = []
    for member in members:
        ids.append(member['id'])

    subscribers = lists.get_subscribers_by_id_list(brand_id, segment.list_id, ids)
    for subscriber in subscribers:
        segment.subscribers.append(subscriber)
    db.session.commit()

    return True, len(subscribers)

def get_subscriber_search_fields(brand_id, segment_id):
    core_fields = ['email_address', 'email_type_preference', 'status']
    fields = []
    status, segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, segment
    for field in core_fields:
        label = field.replace('_', ' ').title()
        fields.append({'Name': field, 'Label': label, 'Required': True})

    return True, fields

def get_subscriber_export_fields(brand_id, segment_id):
    status, segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, segment

    return lists.get_subscriber_export_fields(brand_id, segment.list_id)

def get_subscriber_ids_for_export(brand_id, segment_id):
    status, segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, segment
    subscriber_ids = []
    for subscriber in segment.subscribers.all():
        subscriber_ids.append(subscriber.id)
    return True, subscriber_ids

def get_subscribers(brand_id, segment_id, page, limit):
    merge_fields = []
    total_records = 0
    data = []

    status, current_segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, current_segment
    current_list = lists.list_by_id(brand_id, current_segment.list_id)
    if not current_list:
        return False, "Segment List not found"
    list_merge_fields = current_list.merge_fields.all()
    for list_merge_field in list_merge_fields:
        merge_field = {}
        merge_field['name'] = list_merge_field.name
        merge_field['tag'] = list_merge_field.tag
        merge_fields.append(merge_field)
    query = current_segment.subscribers
    total_records = query.count()
    if limit != 0:
        subscribers = query.paginate(page,limit,False).items
    else:
        subscribers = query.all()

    for subscriber in subscribers:
        data.append(lists.process_subscriber(subscriber, list_merge_fields))
    return True, {'Data': data, 'MergeFields': merge_fields, 'TotalRecords': total_records}

def export_subscribers(export_def, writer, log_writer):
    fields = []
    objects = []
    for field in export_def.fields.all():
        fields.append(field.field_name)

    for obj in export_def.target_objects.all():
        objects.append(obj.object_id)

    writer.writerow(fields)
    status, current_segment = segment_by_id(export_def.brand_id, export_def.target_segment_id)
    if not status:
        return False, current_segment
    return lists._export_subscribers(current_segment.list_id, fields, objects, writer, log_writer)
   
def search_subscribers(brand_id, search_for, search_contains, segment_id):
    status, current_segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, current_segment

    return lists.search_subscribers(search_for, search_contains, current_segment.list_id, current_segment.subscribers)

def remove_subscribers(brand_id, segment_id, subscribers):
    status, current_segment = segment_by_id(brand_id, segment_id)
    if not status:
        return False, current_segment
    if current_segment.type != 'static':
        return False, "Only static segments can be removed from"
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Error getting Brand"
    results = []
    for subscriber in subscribers:
        result = {}
        l_subscriber = current_segment.subscribers.filter(ListSubscriber.id == subscriber).first()
        if not l_subscriber:
            result = {'ID': subscriber, 'Message': 'Not Found'}
        else:
            l_list = List.query.get(l_subscriber.list_id)
            if not l_list:
                result = {'ID': l_subscriber.email_address, 'Message': 'List not found'}
            else:
                data_type = 'lists/%s/segments/%s/members' % (l_list.mailchimp_id, current_segment.mailchimp_id)
                status, response = f.delete_to_mailchimp(brand, data_type, l_subscriber.email_id)
                if not status:
                    result = {'ID': l_subscriber.email_address, 'Message': "Mailchimp Removal Failed - %s" % response}
                else:
                    try:
                        current_segment.subscribers.remove(l_subscriber)
                        db.session.commit()
                        result = {'ID': l_subscriber.email_address, 'Message': "OK"}
                    except Exception as e:
                        result = {'ID': l_subscriber.email_address, 'Message': "DB Removal Failed - %s" % str(e)}
        results.append(result)
    return True, results



def subscriber_segments(brand_id, subscriber_id):
    segments = []
    all_segments = Segment.query.filter(Segment.brand_id == brand_id).all()
    for segment in all_segments:
        if segment.subscribers.filter(ListSubscriber.id == subscriber_id).count() > 0:
            segments.append({'name': segment.name, 'id': segment.id})
    return segments
