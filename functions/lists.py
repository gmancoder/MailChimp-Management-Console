#!/usr/bin/env python
from models.shared import db
from models.lists import *
from models.list_subscribers import *
from models.folders import *
from models.forms import *
from models.users import *
import activities
import core as f
import forms
import json
import datetime
import folders
import re
import campaigns
from sqlalchemy import *
from sqlalchemy import func

def fields():
    fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'List Name', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'contact_company': {'Label': 'Company', 'Required': True, 'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'contact_address1': {'Label': 'Address 1', 'Required': True,
                         'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 2,
        }},
    'contact_address2': {'Label': 'Address 2', 'Required': False,
                         'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 3,
        }},
    'contact_city': {'Label': 'City', 'Required': True, 'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 4,
        }},
    'contact_state': {'Label': 'State', 'Required': True, 'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'select',
        'Type': 'select',
        'Rank': 5,
        'Options': forms.state_territory_dict(),
        }},
    'contact_zip': {'Label': 'Zip', 'Required': True, 'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 12,
        'Rank': 6,
        }},
    'contact_country': {'Label': 'Country', 'Required': True, 'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'select',
        'Type': 'select',
        'Options': forms.create_country_dict(),
        'Rank': 7,
        }},
    'contact_phone': {'Label': 'Phone Number', 'Required': False,
                      'Form': {
        'Group': {'Name': 'Contact', 'Rank': 2},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 20,
        'Rank': 8,
        }},
    'campaign_default_from_name': {'Label': 'From Name',
                                   'Required': True, 'Form': {
        'Group': {'Name': 'Campaign Defaults', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'campaign_default_from_email': {'Label': 'From Email',
                                    'Required': True, 'Form': {
        'Group': {'Name': 'Campaign Defaults', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 2,
        }},
    'campaign_default_subject': {'Label': 'Subject', 'Required': True,
                                 'Form': {
        'Group': {'Name': 'Campaign Defaults', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 3,
        }},
    'campaign_default_language': {'Label': 'Language',
                                  'Required': True, 'Form': {
        'Group': {'Name': 'Campaign Defaults', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 4,
        }},
    'permission_reminder': {'Label': 'Permission Reminder',
                            'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 1024,
        'Rank': 2,
        }},
    'notify_on_subscribe': {'Label': 'Notify On Subscribe',
                            'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 3,
        }},
    'notify_on_unsubscribe': {'Label': 'Notify On Unsubscribe',
                              'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 4,
        }},
    'email_type_option': {'Label': 'Email Type Option',
                          'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'input',
        'Type': 'checkbox',
        'Rank': 5,
        }},
    'visibility': {'Label': 'Visibility', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {'prv': 'Private', 'pub': 'Public'},
        'Rank': 6,
        }},
    }

    return fields

def list_by_id(brand_id, list_id):
    return List.query.filter(and_(List.brand_id == brand_id, List.id == list_id)).first()

def list_defaults_by_id(brand_id, list_id):
    return ListCampaignDefaults.query.filter(ListCampaignDefaults.list_id == list_id).first()

def list_by_mailchimp_id(brand_id, list_mailchimp_id):
    return List.query.filter(and_(List.brand_id == brand_id, List.mailchimp_id == list_mailchimp_id)).first()

def get_all(brand_id):
    return List.query.filter(List.brand_id == brand_id).all()

def get_all_last_sent(brand_id, last_sent):
    return List.query.filter(and_(List.brand_id == brand_id, or_(List.campaign_last_sent >= last_sent, List.campaign_last_sent == None))).all()

def folder_has_lists(folder_id):
    return List.query.filter(List.folder_id == folder_id).count() > 0

def lists_in_folder(folder_id):
    return List.query.filter(List.folder_id == folder_id).all()

def check_fields_in_add_request(request, api=False): 
    groups = FormGroup.query.filter(FormGroup.form_type == "lists").all()
    for group in groups:
        for field in group.fields:
            field_to_check = 'lists_%s' % field.name
            can_be_blank = False
            if field.field_type == "checkbox":
                can_be_blank = True
            if (field.create or api) and field.required and field_to_check not in request and not can_be_blank:
                #print "1"
                return False, field.label
            elif (field_to_check in request and request[field_to_check] == "" and field.required) and not can_be_blank:
                #print "2"
                return False, field.label
    return True, ""

def check_fields_in_update_request(request, api=False): 
    groups = FormGroup.query.filter(FormGroup.form_type == "lists").all()
    for group in groups:
        for field in group.fields:
            field_to_check = 'lists_%s' % field.name
            can_be_blank = False
            if field.field_type == "checkbox":
                can_be_blank = True
            if (field.update or api) and field.required and field_to_check not in request and not can_be_blank:
                #print "1"
                return False, field.label
            elif (field_to_check in request and request[field_to_check] == "" and field.required) and not can_be_blank:
                #print "2"
                return False, field.label
    return True, ""

def add_list_to_database(brand, request, user):
    list = List()
    list = request_to_list(list, request)
    list.brand_id = brand
    if 'folder_id' in request:
        list.folder_id = request['folder_id']
    else:
        root_list_folder = folders.get_root_folder(brand, "lists")
        list.folder_id = root_list_folder.id
    try:
        list.createdby = user.username
        list.updatedby = user.username
        db.session.add(list)
        db.session.commit()
        return True, {'ID': list.id, "Name": list.name}
    except Exception as e:
        return False, str(e)

def request_to_data(request):
    data = {}
    for k,v in request.items():
        if k.startswith('lists_campaign_default'):
            if 'campaign_defaults' not in data:
                data['campaign_defaults'] = {}
            k = k.replace('lists_campaign_default_', '')
            data['campaign_defaults'][k] = v
        elif k.startswith('lists_contact_'):
            if 'contact' not in data:
                data['contact'] = {}
            k = k.replace('lists_contact_', '')
            data['contact'][k] = v
        else:
            k = k.replace('lists_', '')
            data[k] = v
    if 'lists_email_type_option' not in request:
        data['email_type_option'] = False
    else:
        data['email_type_option'] = True
    return data

def post_list_to_mailchimp(brand, request):
    data = request_to_data(request)
    data_str = json.dumps(data)
    return f.post_to_mailchimp(brand, data_str=data_str, data_type="lists")

def post_list_to_database(brand, mailchimp_id, folder_id, request, user):
    data = {}
    for key, value in request.items():
        key = key.replace('lists_', '')
        data[key] = value
    data['id'] = mailchimp_id
    data['folder_id'] = folder_id
    return add_list_to_database(brand.id, data, user)

def list_to_request(l):
    request = {}
    request['name'] = l.name
    request['permission_reminder'] = l.permission_reminder
    request['notify_on_subscribe'] = l.notify_on_subscribe
    request['notify_on_unsubscribe'] = l.notify_on_unsubscribe
    request['email_type_option'] = l.email_type_option
    request['visibility'] = l.visibility
    
    campaign_defaults = l.campaign_defaults[0]
    request['campaign_default_from_name'] = campaign_defaults.from_name
    request['campaign_default_from_email'] = campaign_defaults.from_email
    request['campaign_default_subject'] = campaign_defaults.subject
    request['campaign_default_language'] = campaign_defaults.language
    
    contact = l.contact[0]
    request['contact_company'] = contact.company
    request['contact_address1'] = contact.address1
    request['contact_address2'] = contact.address2
    request['contact_city'] = contact.city
    request['contact_state'] = contact.state
    request['contact_zip'] = contact.zip
    request['contact_country'] = contact.country
    request['contact_phone'] = contact.phone

    return request

def list_to_export_request(l):
    request = list_to_request(l)
    request['id'] = l.id
    request['mailchimp_id'] = l.mailchimp_id

    return request

def request_to_list(list, request):
    print request
    list.mailchimp_id = request['id']
    list.name = request['name']
    list.permission_reminder = request['permission_reminder']
    list.notify_on_subscribe = request['notify_on_subscribe']
    list.notify_on_unsubscribe = request['notify_on_unsubscribe']
    if 'email_type_option' not in request:
        list.email_type_option = 0
    else:
        list.email_type_option = 1
    list.visibility = request['visibility']
    if 'campaign_last_sent' in request and request['campaign_last_sent'] != None and request['campaign_last_sent'].strip() != "":
        list.campaign_last_sent = request['campaign_last_sent']

    campaign_defaults = ListCampaignDefaults()
    campaign_defaults.from_name = request['campaign_default_from_name']
    campaign_defaults.from_email = request['campaign_default_from_email']
    campaign_defaults.subject = request['campaign_default_subject']
    campaign_defaults.language = request['campaign_default_language']
    list.campaign_defaults.append(campaign_defaults)

    contact = ListContact()
    contact.company = request['contact_company']
    contact.address1 = request['contact_address1']
    if 'contact_address2' in request:
        contact.address2 = request['contact_address2']
    contact.city = request['contact_city']
    contact.state = request['contact_state']
    contact.zip = request['contact_zip']
    contact.country = request['contact_country']
    if 'contact_phone' in request:
        contact.phone = request['contact_phone']

    list.contact.append(contact)
 
    if 'campaign_last_sent' in request and request['campaign_last_sent'].strip() != "":
        list.campaign_last_sent = request['campaign_last_sent']

    return list

def update_list_to_database(request, user, id):
    list = List.query.get(id)
    if list:
        list = request_to_list(list, request)
        try:
            list.updated = datetime.datetime.now()
            list.updatedby = user.username
            db.session.commit()
            return True, {'ID': list.id, "Name": list.name}
        except Exception as e:
            return False, str(e)
    else:
        return False, "List Not Found"

def patch_list_to_mailchimp(brand, id, request):
    data = request_to_data(request)
    data_str = json.dumps(data)
    return f.patch_to_mailchimp(brand, data_str=data_str, data_type="lists", id=id)

def patch_list_to_database(request, user, id, mailchimp_id):
    data = {}
    for key, value in request.items():
        key = key.replace('lists_', '')
        data[key] = value
    data['id'] = mailchimp_id
    return update_list_to_database(data, user, id)

def move_list(id, folder_id):
    list = List.query.get(id)
    if not list:
        return False, "List Not Found"

    list.folder_id = folder_id
    try:
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def delete_list(brand, id):
    list = List.query.get(id)
    if not list:
        return False, "List Not Found"

    try:
        status, res = delete_mailchimp_list(brand, list.mailchimp_id)
        if not status:
            return False, res
        db.session.delete(list)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def delete_mailchimp_list(brand_id, id):
    brand = f.GetBrandByID(brand_id)
    return f.delete_to_mailchimp(brand, data_type="lists", id=id)

def list_count_by_name(brand_id, name):
    return List.query.filter(and_(List.brand_id == brand_id, List.name == name)).count()

def import_lists(import_def, reader, writer):
    brand = f.GetBrandByID(import_def.brand_id)
    user = User.query.get(import_def.created_by)
    results = {'total': 0, 'inserted': 0, 'updated': 0, 'ignored': 0, 'errors': 0}
    if not brand:
        return False, "Brand not found"
    if not user:
        return False, "User not found"
    headers = {}
    row_count = 0
    for row in reader:
        row_count += 1
        if row_count == 1:
            for fld in range(0, len(row)):
                header = row[fld]
                dest = activities.get_mapped_field(header, import_def.mappings, import_def.id)
                if dest != None:
                    headers[header] = {'idx': fld, 'dest': dest}
            continue
        results['total'] += 1
        name_idx = headers['name']['idx']
        existing_lists = list_count_by_name(import_def.brand_id, row[name_idx])
        if import_def.import_type == 2:
            if existing_lists > 0:
                results['ignored'] += 1
                writer.writerow([row_count, ','.join(row), "List '%s' already exists" % row[name_idx]])
                continue
        elif import_def.import_type == 3:
            if existing_lists == 0:
                results['ignored'] += 1
                writer.writerow([row_count, ','.join(row), "List '%s' does not exist" % row[name_idx]])
                continue
        else:
            request = {}
            for src, header in headers.items():
                request_col = 'lists_%s' % header['dest']
                request[request_col] = row[header['idx']]
            if existing_lists == 0:
                status, mc_resp = post_list_to_mailchimp(brand, request)
                if not status:
                    msg = 'MailChimp Create Failed: %s' % mc_resp
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), msg])
                    continue
                else:
                    mc = json.loads(mc_resp)
                    mc_id = mc['id']
                    status, resp = post_list_to_database(brand, mc_id, import_def.target_folder_id, request, user)
                    if status:
                        results['inserted'] += 1
                    else:
                        msg = 'DB Create Failed: %s' % resp
                        results['errors'] += 1
                        writer.writerow([row_count, ','.join(row), msg])
            else:
                current_list = List.query.filter(and_(List.brand_id == brand.id, List.name == row[name_idx])).first()
                if not current_list:
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), "List '%s' not found" % row[name_idx]])
                    continue
                
                status, mc_resp = patch_list_to_mailchimp(brand, current_list.mailchimp_id, request)
                if not status:
                    msg = 'MailChimp Update Failed: %s' % mc_resp
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), msg])
                    continue
                else:
                    status, resp = patch_list_to_database(request, user, current_list.id, current_list.mailchimp_id)
                    if status:
                        results['updated'] += 1
                    else:
                        msg = 'DB Update Failed: %s' % resp
                        results['errors'] += 1
                        writer.writerow([row_count, ','.join(row), msg])
    return True, results

def export_lists(export_def, writer, log_writer):
    fields = []
    objects = []
    results = {'total': 0, 'errors': 0}
    for field in export_def.fields.all():
        fields.append(field.field_name)

    for obj in export_def.target_objects.all():
        objects.append(obj.object_id)

    writer.writerow(fields)
    lists = List.query.filter(List.id.in_(objects)).all()
    idx = 0
    for list in lists:
        idx += 1
        row = []
        error = False
        request = list_to_export_request(list)
        for field in fields:
            if field in request:
                row.append(request[field])
            else:
                error = True
                log_writer.writerow([idx, ','.join(row), '%s not a list field' % field])
        if not error:
            writer.writerow(row)
            results['total'] += 1
        else:
            results['errors'] += 1

    return True, results

def search(brand, search_type, search_for, contains, folder_id):
    fields = ['ID', 'MailChimp ID', 'Name', 'Folder']
    
    query = List.query
    if search_type == '1':
        if search_for == 'name':    
            query = query.filter(and_(List.brand_id == brand, List.name.like('%%%s%%' % contains)))
        elif search_for == 'mailchimp_id':
            query = query.filter(and_(List.brand_id == brand, List.mailchimp_id.like('%%%s%%' % contains)))
    elif search_type == '2':
        if search_for == 'name':    
            query = query.filter(and_(List.brand_id == brand, List.name.like('%%%s%%' % contains), List.folder_id == folder_id))
        elif search_for == 'mailchimp_id':
            query = query.filter(and_(List.brand_id == brand, List.mailchimp_id.like('%%%s%%' % contains), List.folder_id == folder_id))
    lists = query.order_by(List.name.asc()).all()
    rows = []
    for list in lists:
        status, flds = folders.get_folders(brand, folder_id=list.folder_id)
        if not status:
            return False, flds
        row = {}
        row['ID'] = list.id
        row['MailChimp ID'] = list.mailchimp_id
        row['Name'] = "<a href='/lists/%s'>%s</a>" % (list.id, list.name)
        row['Folder'] = flds[0]['name']
        rows.append(row)
    return True, {'Fields': fields, 'Data': rows}

def get_merge_field_by_tag(list_id, tag):
    list_merge_field = ListMergeField.query.filter(and_(ListMergeField.list_id == list_id, ListMergeField.tag == tag)).first()
    if not list_merge_field:
        return False, "Merge Field not found"
    return True, list_merge_field

def merge_field_obj(merge_field, list_id, merge_id, tag, name, type, required, public, display_order, default_value, options):
    merge_field.list_id = list_id
    merge_field.mailchimp_id = merge_id
    merge_field.tag = tag
    merge_field.name = name
    merge_field.type = type
    merge_field.required = required
    if isinstance(required, int):
        merge_field.required = (True if required == 1 else False)
    merge_field.public = public
    if isinstance(public, int):
        merge_field.public = (True if public == 1 else False)
    merge_field.display_order = display_order
    merge_field.default_value = default_value
    if options != None:
        if 'size' in options:
            merge_field.size = options['size']
        if 'default_country' in options:
            merge_field.default_country = options['default_country']
        if 'phone_format' in options:
            merge_field.phone_format = options['phone_format']
        if 'date_format' in options:
            merge_field.date_format = options['date_format']
        if 'choices' in options:
            if merge_field.choices.count() > 0:
                for current_choice in merge_field.choices.all():
                    db.session.delete(current_choice)
                    db.session.commit()
            for choice in options['choices']:
                merge_choice = ListMergeFieldChoice(choice)
                merge_field.choices.append(merge_choice)
    return merge_field

def add_merge_field_to_db(list_id, merge_id, tag, name, type, required, public, display_order, default_value, options, user=None, sync=False):
    merge_field = ListMergeField()
    merge_field = merge_field_obj(merge_field, list_id, merge_id, tag, name, type, required, public, display_order, default_value, options)
    try:
        if user != None:
            merge_field.created_by = user.id
        db.session.add(merge_field)
        db.session.commit()
        #status, merge_result = add_merge_field_to_subscribers(list_id, merge_field)
        #if not status:
        #    return False, merge_result
        if sync:
            return True, merge_field
        return True, f._obj_to_dict([merge_field])
    except Exception as e:
        return False, str(e)



def add_merge_field(brand_id, list_id, tag, name, type, required, public, display_order, default_value, options):
    current_list = List.query.get(list_id)
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Brand not found"
    if not current_list:
        return False, "List Not Found"

    new_merge_field = {'name': name, 
                        'tag': tag,
                        'type': type,
                        'required': (True if required == 1 else False),
                        'public': (True if public == 1 else False),
                        'default_value': default_value,
                        'display_order': display_order,
                        'options': options
                        }
    url_append = 'lists/%s/merge-fields' % (current_list.mailchimp_id)
    status, response = f.post_to_mailchimp(brand, url_append, json.dumps(new_merge_field))
    if not status:
        return False, response
    mc = json.loads(response)
    merge_id = mc['merge_id']
    status, response = add_merge_field_to_db(list_id, merge_id, tag, name, type, required, public, display_order, default_value, options)
    if not status:
        return False, response

    return True, response

def get_single_merge_field(id):
    merge_field = ListMergeField.query.get(id)
    if not merge_field:
        return False, "Merge Field Not Found"
    
    merge_field_choices = []
    for choice in merge_field.choices.all():
        merge_field_choices.append(choice.choice)
    merge_field_dict = f._obj_to_dict([merge_field])
    merge_field_dict[0]['choices'] = '|'.join(merge_field_choices)

    return True, merge_field_dict

def update_merge_field(brand_id, list_id, old_tag, tag, name, type, required, public, display_order, default_value, options, merge_id, id):
    current_list = List.query.get(list_id)
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Brand not found"
    if not current_list:
        return False, "List Not Found"

    if(type not in ('dropdown', 'radio')):
        mc_merge_field = {'name': name, 
                            'tag': tag,
                            'required': (True if required == 1 else False),
                            'public': (True if public == 1 else False),
                            'default_value': default_value,
                            'display_order': display_order,
                            'options': options
                            }
        url_append = 'lists/%s/merge-fields' % (current_list.mailchimp_id)
        status, response = f.patch_to_mailchimp(brand, url_append, json.dumps(mc_merge_field), merge_id)
    else:
        mc_merge_field = {'apikey': brand.api_key,
                            'id': current_list.mailchimp_id,
                            'tag': old_tag,
                            'options': {
                                'choices': options['choices'],
                                'name': name, 
                                'tag': tag,
                                'required': (True if required == 1 else False),
                                'public': (True if public == 1 else False),
                                'default_value': default_value,
                                'display_order': display_order
                            }
                            }
        url_append = 'lists/merge-var-update.json'
        status, response = f.patch_to_mailchimp_2(brand, url_append, json.dumps(mc_merge_field))
    if not status:
        return False, response
    
    status, response = update_merge_field_to_db(id, list_id, merge_id, tag, name, type, required, public, display_order, default_value, options)
    if not status:
        return False, response

    return True, response

def update_merge_field_to_db(id, list_id, merge_id, tag, name, type, required, public, display_order, default_value, options, user=None, sync=False):
    merge_field = ListMergeField.query.get(id)
    if not merge_field:
        return False, "Merge Field not found"
    merge_field = merge_field_obj(merge_field, list_id, merge_id, tag, name, type, required, public, display_order, default_value, options)
    try:
        if user != None:
            merge_field.updated_by = user.id
        merge_field.updated = datetime.datetime.now()
        db.session.commit()
        if sync:
            return True, merge_field
        return True, f._obj_to_dict([merge_field])
    except Exception as e:
        return False, str(e)

def delete_merge_field(brand_id, list_id, merge_id, id):
    current_list = List.query.get(list_id)
    brand = f.GetBrandByID(brand_id)
    merge_field = ListMergeField.query.get(id)
    if not brand:
        return False, "Brand not found"
    if not current_list:
        return False, "List Not Found"
    if not merge_field:
        return False, "Merge Field not found"

    url_append = 'lists/%s/merge-fields' % (current_list.mailchimp_id)
    status, response = f.delete_to_mailchimp(brand, url_append, merge_id)
    if not status:
        return False, response

    try:
        subscriber_fields = ListSubscriberMergeField.query.filter(ListSubscriberMergeField.list_merge_field_id == merge_field.id).all()
        for s_field in subscriber_fields:
            db.session.delete(s_field)
            db.session.commit()
        db.session.delete(merge_field)
        db.session.commit()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def get_merge_fields_for_content(brand_id, list_id=None):
    lists = {}
    query = List.query
    if list_id != None:
        query = query.filter(and_(List.brand_id == brand_id, List.id == list_id))
    else:
        query = query.filter(List.brand_id == brand_id)
    all_lists = query.order_by(List.name.asc()).all()
    for lst in all_lists:
        lists[lst.name] = {'alias': re.sub('[^0-9A-Za-z]', '_', lst.name), 'tags': {}}
        for merge_field in lst.merge_fields.all():
            lists[lst.name]['tags'][merge_field.tag] = merge_field.name
    return lists

def check_required_fields(list_id, merge_fields):
    merge_field_tags = []
    if merge_fields != None:
        for tag, value in merge_fields.items():
            if value != None and value.strip() != "":
                merge_field_tags.append(tag)
    required_fields_missing = ListMergeField.query.filter(and_(ListMergeField.list_id == list_id, ListMergeField.required == True, ListMergeField.tag.notin_(merge_field_tags))).count()
    if required_fields_missing > 0:
        return False, "Some required fields missing"
    return True, merge_field_tags

def add_subscriber_to_db(brand_id, list_id, email_id, email_address, unique_email_id, email_type, email_status, timestamp_signup, last_changed, location, merge_fields, user, sync=False):
    status, merge_field_tags = check_required_fields(list_id, merge_fields)
    ##print merge_field_tags
    ##print merge_fields
    if not status:
        return False, merge_field_tags

    new_subscriber = ListSubscriber()
    new_subscriber.brand_id = brand_id
    new_subscriber.list_id = list_id
    new_subscriber.email_id = email_id
    new_subscriber.email_address = email_address
    new_subscriber.unique_email_id = unique_email_id
    new_subscriber.email_type = email_type
    new_subscriber.status = email_status
    if timestamp_signup != None and timestamp_signup != "":
        new_subscriber.created = timestamp_signup
    if last_changed != None:
        new_subscriber.updated = last_changed

    if len(location) > 0:
        new_location = ListSubscriberLocation()
        new_location = location_dict_to_object(location, new_location)
        new_subscriber.location.append(new_location)
    new_subscriber.created_by = user.id
    db.session.add(new_subscriber)
    db.session.commit()

    all_merge_fields = ListMergeField.query.filter(ListMergeField.list_id == list_id).all()
    for merge_field in all_merge_fields:
        value = merge_field.default_value
        if(merge_field.tag in merge_field_tags):
            value = merge_fields[merge_field.tag]
        ##print '%s: %s' % (merge_field.tag, value)
        status, results = add_merge_field_to_subscriber(new_subscriber, merge_field, value)
        if not status:
            return False, results
    if sync:
        return True, new_subscriber
    return True, f._obj_to_dict([new_subscriber])

def location_dict_to_object(location_dict, location_obj):
    location_obj.latitude = location_dict['latitude']
    location_obj.longitude = location_dict['longitude']
    location_obj.gmtoff = location_dict['gmtoff']
    location_obj.dstoff = location_dict['dstoff']
    location_obj.country_code = location_dict['country_code']
    location_obj.timezone = location_dict['timezone']
    return location_obj

def add_merge_field_to_subscribers(list_id, list_merge_field):
    current_list = List.query.get(list_id)
    if not current_list:
        return False, "List Not Found"

    for subscriber in current_list.subscribers.all():
        status, response = add_merge_field_to_subscriber(subscriber, list_merge_field, list_merge_field.default_value)
        if not status:
            return False, response
    return True, "Added '%s' to All List Subscribers" % list_merge_field.name

def add_merge_field_to_subscriber(subscriber, list_merge_field, value=None):
    merge_field = ListSubscriberMergeField()
    merge_field.list_merge_field_id = list_merge_field.id
    merge_field.list_subscriber_id = subscriber.id
    if value != None and value.strip != "":
        merge_field.value = value
    else:
        merge_field.value = list_merge_field.default_value
    #subscriber.merge_fields.append(merge_field)
    try:
        db.session.add(merge_field)
        db.session.commit()
        return True, ""
    except Exception as e:
        return False, str(e)

def get_status_data(list_id):
    current_list = List.query.get(list_id)
    if not current_list:
        return False, "List Not Found"

    statuses = {}
    subscribers = current_list.subscribers.all()
    for subscriber in subscribers:
        if subscriber.status not in statuses:
            statuses[subscriber.status] = 0
        statuses[subscriber.status] += 1
    status_data = []
    for status, count in statuses.items():
        stat = {'status': status, 'count': count}
        status_data.append(stat)
    return True, status_data

def get_subscriber_by_id(brand_id, list_subscriber_id):
    list_subscriber = ListSubscriber.query.filter(and_(ListSubscriber.brand_id == brand_id, ListSubscriber.id == list_subscriber_id)).first()
    if not list_subscriber:
        return False, "Subscriber not found"
    return True, list_subscriber

def get_subscriber_by_email_id(brand_id, email_id, list_id=None):
    if list_id != None:
        current_list = list_by_mailchimp_id(brand_id, list_id)
        if not current_list:
            return False, "List not found"
        list_subscriber = ListSubscriber.query.filter(and_(ListSubscriber.list_id == current_list.id, ListSubscriber.brand_id == brand_id, ListSubscriber.email_id == email_id)).first()
    else:
        list_subscriber = ListSubscriber.query.filter(and_(ListSubscriber.brand_id == brand_id, ListSubscriber.email_id == email_id)).first()
    if not list_subscriber:
        return False, "Subscriber not found"
    return True, list_subscriber

def get_subscribers(list_id, page, limit):
    current_list = List.query.get(list_id)
    if not current_list:
        return False, "List Not Found"
    list_merge_fields = current_list.merge_fields.all()
    subs = []
    query = current_list.subscribers
    total_records = query.count()
    if limit != 0:
        subscribers = query.paginate(page,limit,False).items
    else:
        subscribers = query.all()
    
    for subscriber in subscribers:
        subs.append(process_subscriber(subscriber, list_merge_fields))
    return True, {'Data': subs, 'MergeFields': f._obj_to_dict(list_merge_fields), 'TotalRecords': total_records}

def get_subscribers_by_id_list(brand_id, list_id, id_list):
    return ListSubscriber.query.filter(and_(ListSubscriber.brand_id == brand_id, ListSubscriber.list_id == list_id, ListSubscriber.email_id.in_(id_list))).all()

def process_subscriber(subscriber, list_merge_fields):
    subscriber_fields = _subscriber_fields_to_iv_dict(subscriber.merge_fields.all())
    sub = {'ID': subscriber.id, 'EmailId': subscriber.email_id, 'EmailAddress': subscriber.email_address, 'Status': subscriber.status, 'EmailTypePreference': subscriber.email_type, 'DateAdded': str(subscriber.created), 'LastModified': str(subscriber.updated)}
    sub = process_subscriber_merge_fields(sub, list_merge_fields, subscriber_fields)
    return sub

def process_subscriber_merge_fields(sub, list_merge_fields, subscriber_fields=[]):
    for merge_field in list_merge_fields:
        if merge_field.id in subscriber_fields:
            sub[merge_field.tag] = subscriber_fields[merge_field.id]
        else:
            sub[merge_field.tag] = merge_field.default_value
    return sub

def _subscriber_fields_to_iv_dict(subscriber_fields):
    sub_fields = {}
    for field in subscriber_fields:
        sub_fields[field.list_merge_field_id] = field.value

    return sub_fields

def add_subscriber_to_mailchimp(current_list, merge_fields, new_subscriber):
    brand = f.GetBrandByID(current_list.brand_id)
    if not brand:
        return False, "An error occurred rendering Brand"
    mailchimp_subscriber = {}
    mailchimp_subscriber['email_address'] = new_subscriber['EmailAddress']
    mailchimp_subscriber['email_type'] = new_subscriber['EmailTypePreference']
    mailchimp_subscriber['status'] = new_subscriber['Status']
    mailchimp_subscriber['merge_fields'] = {}
    for merge_field in merge_fields:
        if merge_field.tag in new_subscriber:
            mailchimp_subscriber['merge_fields'][merge_field.tag] = new_subscriber[merge_field.tag]
    if 'location' in new_subscriber and len(new_subscriber['location']) > 0:
        mailchimp_subscriber['location'] = new_subscriber['location']
    return f.post_to_mailchimp(brand, "lists/%s/members" % current_list.mailchimp_id, json.dumps(mailchimp_subscriber))

def update_subscriber_to_mailchimp(current_list, merge_fields, subscriber, email_id):
    brand = f.GetBrandByID(current_list.brand_id)
    if not brand:
        return False, "An error occurred rendering Brand"
    mailchimp_subscriber = {}
    mailchimp_subscriber['email_type'] = subscriber['EmailTypePreference']
    mailchimp_subscriber['status'] = subscriber['Status']
    mailchimp_subscriber['merge_fields'] = {}
    for merge_field in merge_fields:
        if merge_field.tag in subscriber:
            mailchimp_subscriber['merge_fields'][merge_field.tag] = subscriber[merge_field.tag]
    mailchimp_subscriber['location'] = subscriber['location']
    return f.patch_to_mailchimp(brand, "lists/%s/members" % (current_list.mailchimp_id), json.dumps(mailchimp_subscriber), email_id)

def update_subscriber_to_db(subscriber_id, email_type, email_status, last_changed, location, merge_fields, user, sync=False):
    subscriber = ListSubscriber.query.get(subscriber_id)
    if not subscriber:
        return False, "Error retrieving Subscriber"

    subscriber.email_type = email_type
    subscriber.status = email_status
    subscriber.updated = last_changed
    subscriber.updated_by = user.id
    try:
        db.session.commit()
    except Exception as e:
        return False, str(e)

    for s_merge_field in subscriber.merge_fields.all():
        if s_merge_field.list_merge_field_id in merge_fields:
            s_merge_field.value = merge_fields[s_merge_field.list_merge_field_id]
            try:
                db.session.commit()
            except Exception as e:
                return False, str(e)

    for s_location in subscriber.location.all():
        if len(location) > 0:
            s_location = location_dict_to_object(location, s_location)
            try:
                db.session.commit()
            except Exception as e:
                return False, str(e)
    if sync:
        return True, subscriber
    return True, f._obj_to_dict([subscriber])

def trans_merge_field_tag_to_id_dict(list_id, merge_fields):
    new_merge_fields = {}
    for tag, value in merge_fields.items():
        list_merge_field = ListMergeField.query.filter(and_(ListMergeField.list_id == list_id, ListMergeField.tag == tag)).first()
        if not list_merge_field:
            continue
        new_merge_fields[list_merge_field.id] = value
    #print new_merge_fields
    return new_merge_fields

def delete_subscribers(brand_id, subscribers):
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Error getting Brand"
    results = []
    for subscriber in subscribers:
        result = {}
        l_subscriber = ListSubscriber.query.get(subscriber)
        if not l_subscriber:
            result = {'ID': subscriber, 'Message': 'Not Found'}
        else:
            l_list = List.query.get(l_subscriber.list_id)
            if not l_list:
                result = {'ID': l_subscriber.email_address, 'Message': 'List not found'}
            else:
                data_type = 'lists/%s/members' % l_list.mailchimp_id
                status, response = f.delete_to_mailchimp(brand, data_type, l_subscriber.email_id)
                if not status:
                    result = {'ID': l_subscriber.email_address, 'Message': "Mailchimp Delete Failed - %s" % response}
                else:
                    try:
                        db.session.delete(l_subscriber)
                        db.session.commit()
                        result = {'ID': l_subscriber.email_address, 'Message': "OK"}
                    except Exception as e:
                        result = {'ID': l_subscriber.email_address, 'Message': "DB Delete Failed - %s" % str(e)}
        results.append(result)
    return True, results

def subscriber_import_mapping(list_id):
    fields = []
    fields.append({'Name': 'email_address', 'Label': 'Email Address', 'Required': True});
    fields.append({'Name': 'email_type', 'Label': 'Email Type Preference', 'Required': True});
    fields.append({'Name': 'status', 'Label': 'Status', 'Required': True});
    fields.append({'Name': 'latitude', 'Label': 'Location Latitude', 'Required': False});
    fields.append({'Name': 'longitude', 'Label': 'Location Longitude', 'Required': False});
    current_list = List.query.get(list_id)
    if not current_list:
        return []
    merge_fields = current_list.merge_fields.order_by(ListMergeField.display_order.asc()).all()
    for merge_field in merge_fields:
        fields.append({'Name': merge_field.tag, 'Label': merge_field.name, 'Required': merge_field.required})

    return fields

def subscriber_exists(brand_id, list_id, email_address):
    count = ListSubscriber.query.filter(and_(ListSubscriber.list_id == list_id, func.lower(ListSubscriber.email_address) == func.lower(email_address))).count()
    return count > 0

def import_subscribers(import_def, reader, writer):
    brand = f.GetBrandByID(import_def.brand_id)
    user = User.query.get(import_def.created_by)
    current_list = List.query.get(import_def.target_list_id)
    results = {'total': 0, 'inserted': 0, 'updated': 0, 'ignored': 0, 'errors': 0}
    if not brand:
        return False, "Brand not found"
    if not user:
        return False, "User not found"
    if not current_list:
        return False, "List not found"
    headers = {}
    row_count = 0
    for row in reader:
        row_count += 1
        if row_count == 1:
            for fld in range(0, len(row)):
                header = row[fld]
                dest = activities.get_mapped_field(header, import_def.mappings, import_def.id)
                if dest != None:
                    headers[header] = {'idx': fld, 'dest': dest}
            continue
        results['total'] += 1
        email_idx = headers['email_address']['idx']
        email_exists = subscriber_exists(import_def.brand_id, import_def.target_list_id, row[email_idx])
        if import_def.import_type == 2:
            if email_exists:
                results['ignored'] += 1
                writer.writerow([row_count, ','.join(row), "Subscriber '%s' already exists" % row[email_idx]])
                continue
        elif import_def.import_type == 3:
            if not email_exists:
                results['ignored'] += 1
                writer.writerow([row_count, ','.join(row), "Subscriber '%s' does not exist" % row[email_idx]])
                continue
        else:
            request = {}
            new_subscriber = {}
            new_subscriber['location'] = {}
            merge_fields = {}
            for src, header in headers.items():
                ##print header
                if header['dest'] == 'email_address':
                    new_subscriber['EmailAddress'] = row[header['idx']]
                elif header['dest'] == 'status':
                    new_subscriber['Status'] = row[header['idx']]
                elif header['dest'] == 'email_type':
                    new_subscriber['EmailTypePreference'] = row[header['idx']]
                elif header['dest'] in ('latitude', 'longitude'):
                    new_subscriber['location'][header['dest']] = row[header['idx']]
                else:
                    new_subscriber[header['dest']] = row[header['idx']]
                    merge_fields[header['dest']] = row[header['idx']]
            ##print merge_fields
            if not email_exists:
                ##print new_subscriber
                status, mc_resp = add_subscriber_to_mailchimp(current_list, current_list.merge_fields.all(), new_subscriber)
                if not status:
                    msg = 'MailChimp Create Failed: %s' % mc_resp
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), msg])
                    continue
                else:
                    mailchimp_response = json.loads(mc_resp)
                    email_id = mailchimp_response['id']
                    unique_email_id = mailchimp_response['unique_email_id']
                    email_address = mailchimp_response['email_address']
                    email_type = mailchimp_response['email_type']
                    email_status = mailchimp_response['status']
                    timestamp_signup = mailchimp_response['timestamp_opt']
                    location = mailchimp_response['location']
                    last_changed = mailchimp_response['last_changed']
                    
                    status, resp = add_subscriber_to_db(current_list.brand_id, current_list.id, email_id, email_address, unique_email_id, email_type, email_status, timestamp_signup, last_changed, location, merge_fields, user)
                    if status:
                        results['inserted'] += 1
                    else:
                        msg = 'DB Create Failed: %s' % resp
                        results['errors'] += 1
                        writer.writerow([row_count, ','.join(row), msg])
            else:
                current_subscriber = ListSubscriber.query.filter(and_(ListSubscriber.list_id == import_def.target_list_id, func.lower(ListSubscriber.email_address) == func.lower(row[email_idx]))).first()
                if not current_subscriber:
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), "Subscriber '%s' not found" % row[email_idx]])
                    continue
                new_subscriber['merge_fields'] = merge_fields
                status, mc_resp = update_subscriber_to_mailchimp(current_list, current_list.merge_fields.all(), new_subscriber, current_subscriber.email_id)
                if not status:
                    msg = 'MailChimp Update Failed: %s' % mc_resp
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), msg])
                    continue
                else:
                    mailchimp_response = json.loads(mc_resp)
                    location = mailchimp_response['location']
                    last_changed = mailchimp_response['last_changed']
                    status, resp = update_subscriber_to_db(current_subscriber.id, new_subscriber["EmailTypePreference"], new_subscriber["Status"], last_changed, location, trans_merge_field_tag_to_id_dict(current_list.id, merge_fields), user)
                    if status:
                        results['updated'] += 1
                    else:
                        msg = 'DB Update Failed: %s' % resp
                        results['errors'] += 1
                        writer.writerow([row_count, ','.join(row), msg])
    return True, results

def get_subscriber_export_fields(brand_id, list_id):
    core_fields = ['id', 'email_id', 'email_address', 'email_type_preference', 'status', 'date_added', 'last_modified']
    fields = []
    current_list = List.query.filter(and_(List.brand_id == brand_id, List.id == list_id)).first()
    if not current_list:
        return False, "List not found"
    merge_fields = current_list.merge_fields.all()
    for field in core_fields:
        label = field.replace('_', ' ').title()
        fields.append({'Name': field, 'Label': label, 'Required': True})

    for field in merge_fields:
        fields.append({'Name': field.tag, 'Label': field.name, 'Required': field.required})

    return True, fields

def get_subscriber_search_fields(list_id):
    core_fields = ['email_address', 'email_type_preference', 'status']
    fields = []
    current_list = List.query.get(list_id)
    if not current_list:
        return False, "List not found"
    for field in core_fields:
        label = field.replace('_', ' ').title()
        fields.append({'Name': field, 'Label': label, 'Required': True})

    return True, fields

def get_subscriber_ids_for_export(list_id):
    current_list = List.query.get(list_id)
    if not current_list:
        return False, "List not found"
    subscriber_ids = []
    for subscriber in current_list.subscribers.all():
        subscriber_ids.append(subscriber.id)
    return True, subscriber_ids

def export_subscribers(export_def, writer, log_writer):
    fields = []
    objects = []
    for field in export_def.fields.all():
        fields.append(field.field_name)

    for obj in export_def.target_objects.all():
        objects.append(obj.object_id)

    writer.writerow(fields)
    return _export_subscribers(export_def.target_list_id, fields, objects, writer, log_writer)

def _export_subscribers(list_id, fields, objects, writer, log_writer):
    results = {'total': 0, 'errors': 0}
    current_list = List.query.get(list_id)
    if not current_list:
        return False, "List not found"
    merge_fields = current_list.merge_fields.all()   
    subscribers = ListSubscriber.query.filter(and_(ListSubscriber.list_id == list_id, ListSubscriber.id.in_(objects))).all()
    idx = 0
    for subscriber in subscribers:
        idx += 1
        row = []
        error = False
        request = process_subscriber(subscriber, merge_fields)
        for field in fields:
            camel_field = f.camel(field)
            if field in request:
                row.append(str(request[field]))
            elif camel_field in request:
                row.append(str(request[camel_field]))
            else:
                error = True
                log_writer.writerow([str(idx), ','.join(row), '%s not a subscriber field' % field])
        if not error:
            writer.writerow(row)
            results['total'] += 1
        else:
            results['errors'] += 1

    return True, results

def search_subscribers(search_for, contains, list_id, query=None):
    final_fields = ['ID', 'Email Address', "Email Type Preference", "Status"]
    if query == None:
        query = ListSubscriber.query
    if search_for == 'email_address':
        query = query.filter(and_(ListSubscriber.list_id == list_id, ListSubscriber.email_address.like('%%%s%%' % contains)))
    elif search_for == 'email_type_preference':
        query = query.filter(and_(ListSubscriber.list_id == list_id, ListSubscriber.email_type.like('%%%s%%' % contains)))
    elif search_for == 'status':
        query = query.filter(and_(ListSubscriber.list_id == list_id, ListSubscriber.status.like('%%%s%%' % contains)))
    
    query = query.order_by(ListSubscriber.email_address.asc()).all()
    rows = []
    for subscriber in query:
        row = {}
        row['ID'] = subscriber.id
        row['Email Address'] = '<a href="/subscribers/%s">%s</a>' % (subscriber.id, subscriber.email_address)
        row['Email Type Preference'] = subscriber.email_type
        row['Status'] = subscriber.status
        rows.append(row)
    
    return True, {'Fields': final_fields, 'Data': rows}

def post_activity(brand_id, list_id, day, emails_sent, unique_opens, recipient_clicks, hard_bounce, soft_bounce, subs, unsubs, other_adds, other_removes, user):
    current_list = list_by_id(brand_id, list_id)
    if not current_list:
        return False, "List not found"
    update = True
    current_activity = current_list.activity.filter(ListActivity.day == day).first()
    if not current_activity:
        update = False
        current_activity = ListActivity()
        current_activity.list_id = list_id
        current_activity.created_by = user.id
        current_activity.day = day
    current_activity.emails_sent = emails_sent
    current_activity.unique_opens = unique_opens
    current_activity.recipient_clicks = recipient_clicks
    current_activity.hard_bounce = hard_bounce
    current_activity.soft_bounce = soft_bounce
    current_activity.subs = subs
    current_activity.unsubs = unsubs
    current_activity.other_adds = other_adds
    current_activity.other_removes = other_removes
    current_activity.updated = datetime.datetime.now()
    current_activity.updated_by = user.id
    try:
        if not update:
            db.session.add(current_activity)
        db.session.commit()
        return True, current_activity
    except Exception as ex:
        return False, str(ex)

def post_subscriber_activity(brand_id, list_subscriber_id, action, timestamp, url, type, campaign_mailchimp_id, title, user):
    status, list_subscriber = get_subscriber_by_id(brand_id, list_subscriber_id)
    if not status:
        return False, list_subscriber
    campaign_type = "regular"
    status, campaign = campaigns.campaign_by_mailchimp_id(brand_id, campaign_mailchimp_id)
    if not status:
        campaign_type = "variate"
        status, campaign = campaigns.variate_by_mailchimp_id(brand_id, campaign_mailchimp_id)
        if not status:
            #print campaign_mailchimp_id
            return False, campaign

    if campaign_type == 'regular':
        current_activity = list_subscriber.activity.filter(and_(ListSubscriberActivity.action == action, ListSubscriberActivity.timestamp == timestamp, ListSubscriberActivity.campaign_id == campaign.id)).first()
    elif campaign_type == 'variate':
        current_activity = list_subscriber.activity.filter(and_(ListSubscriberActivity.action == action, ListSubscriberActivity.timestamp == timestamp, ListSubscriberActivity.variate_campaign_id == campaign.id)).first()
    if not current_activity:
        current_activity = ListSubscriberActivity()
        current_activity.list_subscriber_id = list_subscriber_id
        current_activity.action = action
        current_activity.created_by = user.id
        current_activity.timestamp = timestamp
        current_activity.url = url
        current_activity.type = type
        current_activity.title = title
        if campaign_type == "regular":
            current_activity.campaign_id = campaign.id
        elif campaign_type == 'variate':
            current_activity.variate_campaign_id = campaign.id

        try:
            db.session.add(current_activity)
            db.session.commit()
            return True, current_activity
        except Exception as ex:
            return False, str(ex)
    return True, None
    #else:
    #    return False, "Already exists"