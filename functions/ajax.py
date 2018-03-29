#!/usr/bin/env python
import re
import unidecode
from models.shared import db
from models.users import *
from models.api_log import *
import datetime
import json
from flask import redirect, url_for, g, request, flash
from flask_login import current_user
import core as f
import lists
import folders
import activities
import forms
import templates
import math
import system
import emails
import segments
import campaigns
import tracking
import tools
import users
import file_locations

def RequestToLog(action, method, request_object):
    api_log = APILog()
    api_log.created_by = g.user.id
    api_log.action = action
    api_log.method = method
    for key, value in request_object.items():
        if key not in ('action', 'method'):
            if isinstance(value, list):
                for v in value:
                    api_log.request_fields.append(APIRequestField(key, v))
            else:
                if len(value) > 4000:
                    parts_count = int(math.floor(float(len(value)) / float(4000)))
                    for idx in range(0, parts_count):
                        new_key = '%s_%s' % (key, idx)
                        start = idx * 4000
                        end = start + 4000
                        new_value = value[start:end]
                        api_log.request_fields.append(APIRequestField(new_key, new_value))
                else:
                    api_log.request_fields.append(APIRequestField(key, value))
    try:
        db.session.add(api_log)
        db.session.commit()
        return True, api_log
    except Exception as e:
        return False, str(e)

def Request(action, method, response_type):
    global request
    request_object = BuildRequestObject(action, method, response_type)
    status, api_log = RequestToLog(action, method, request_object)
    if not status:
        status_type = "Error"
        results = [{'Message': api_log}]
    else:
        status, status_type, results = ProcessRequest(action, method, request_object)
        try:
            api_log.status = status
            api_log.status_type = status_type
            str_results = json.dumps(results)
            if len(str_results) > 4000:
                str_results = str_results[0:4000]
            api_log.response = str_results
            db.session.commit()
        except Exception as e:
            status = False
            status_type = "Error"
            results = [{'Message': str(e)}]
    return status, status_type, request_object, results

def BuildRequestObject(action, method, response_type):
    req = {}
    req['action'] = action
    req['method'] = method
    req['response_type'] = response_type
    for key,value in request.form.items():
        if '[]' in key:
            req[key] = request.form.getlist(key)
        else:
            req[key] = request.form[key]
    return req

def ProcessRequest(action, method, request_object):
    if 'brand' in request_object:
        brand = request_object['brand']
        if action == 'file_locations':
            if method == 'delete':
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = file_locations.delete_file_location(id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action in ('manage_users', 'users'):
            if method == 'delete':
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    if g.user.id == int(id):
                        return False, "Error", [{'Message': 'Cannot delete self'}]
                    status, resp = users.delete_user(id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "tool_settings":
            if method == 'add':
                if 'tool_id' not in request_object:
                    return False, "Error", [{'Message': 'tool_id not specified'}]
                tool_id = request_object['tool_id']
                if 'key' not in request_object:
                    return False, "Error", [{'Message': 'key not specified'}]
                key = request_object['key']
                if 'value' not in request_object:
                    return False, "Error", [{'Message': 'value not specified'}]
                value = request_object['value']
                status, response = tools.add_setting(tool_id, key, value, g.user)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == 'delete':
                if 'id' not in request_object:
                    return False, "Error", [{'Message': 'id not specified'}]
                id = request_object['id']
                status, response = tools.delete_setting(id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", {'ID': id}
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "lists":
            if method == "get":
                all_lists = lists.get_all(brand)
                return True, "OK", f._obj_to_dict(all_lists)
            elif method == 'get_single':
                if 'id' not in request_object:
                    return False, "Error", [{'Message': 'id not specified'}]
                list_id = request_object['id']
                current_list = lists.list_by_id(brand, list_id)
                if not current_list:
                    return False, "Error", [{'Message': "List not found"}]
                return True, "OK", f._obj_to_dict([current_list])
            elif method == 'get_defaults':
                if 'id' not in request_object:
                    return False, "Error", [{'Message': 'id not specified'}]
                list_id = request_object['id']
                current_defaults = lists.list_defaults_by_id(brand, list_id)
                if not current_defaults:
                    return False, "Error", [{'Message': "List not found"}]
                return True, "OK", f._obj_to_dict([current_defaults])
            elif method == "add":
                status, field = lists.check_fields_in_add_request(request_object, True)
                if status:
                    status, new_list = lists.add_list_to_database(brand, request_object, g.user)
                    if status:
                        return True, "OK", new_list
                    else:
                        return False, "Error", [{'Message': new_list}]
                else:
                    return False, "Error", [{"Message": "Field '%s' missing from request" % field}]
            elif method == "move":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = lists.move_list(id, folder_id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "delete":
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = lists.delete_list(brand, id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            elif method == "search":
                if 'search_type' not in request_object:
                    return False, "Error", [{'Message': 'search_type not specified'}]
                search_type = request_object['search_type']
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                search_folder_id = None
                if search_type == '2' and 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                elif search_type == '2':
                    search_folder_id = request_object['search_folder_id']

                #try:
                status, results = lists.search(brand, search_type, search_for, search_contains, search_folder_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
                #except Exception as e:
                #    return False, "Error", [{'Message': str(e)}]
            elif method == "statuses":
                if 'list_id' not in request_object:
                    return False, "Error", [{'Message': 'list_id not specified'}]
                list_id = request_object['list_id']
                status, results = lists.get_status_data(list_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]   
        elif action == "list_merge_fields":
            if 'list_id' not in request_object:
                return False, "Error", [{'Message': 'List ID not specified'}]
            list_id = request_object['list_id']
            if method in ('add', 'post', 'patch', 'sync'):
                if 'tag' not in request_object:
                    return False, "Error", [{'Message': "tag not specified"}]
                tag = request_object['tag']
                if 'name' not in request_object:
                    return False, "Error", [{'Message': "name not specified"}]
                name = request_object['name']
                if 'type' not in request_object:
                    return False, "Error", [{'Message': "type not specified"}]
                type = request_object['type']
                if 'required' not in request_object:
                    return False, "Error", [{'Message': "required not specified"}]
                required = int(request_object['required'])
                if 'public' not in request_object:
                    return False, "Error", [{'Message': "public not specified"}]
                public = int(request_object['public'])
                if 'display_order' not in request_object:
                    return False, "Error", [{'Message': "display_order not specified"}]
                display_order = int(request_object['display_order'])
                default_value = ""
                if 'default_value' in request_object:
                    default_value = request_object['default_value']
                
            if method in ('add', 'patch', 'sync', 'delete'):
                if 'merge_id' not in request_object:
                    return False, "Error", [{'Message': "merge_id not specified"}]
                merge_id = request_object['merge_id']

            if method in ('patch', 'get_single', 'delete'):
                if 'id' not in request_object:
                    return False, "Error", [{'Message': 'id not specified'}]
                id = request_object['id']

            if method in ('post', 'patch'):
                options = {}
                if 'choice[]' in request_object:
                    options['choices'] = request_object['choice[]']
                if 'size' in request_object:
                    size = int(request_object['size'])
                    if size > 0:
                        options['size'] = size
                if 'default_country' in request_object:
                    default_country = request_object['default_country']
                    if default_country != "":
                        options['default_country'] = default_country
                if 'date_format' in request_object:
                    date_format = request_object['date_format']
                    if date_format != "":
                        options['date_format'] = date_format
                if 'phone_format' in request_object:
                    phone_format = request_object['phone_format']
                    if phone_format != "":
                        options['phone_format'] = phone_format

            if method == "add":
                options = None
                if 'options' in request_object:
                    try:
                        options = json.loads(request_object['options'])
                    except Exception as e:
                        return False, "Error", [{'Message': 'Options exist but could not be tranlated - %s' % str(e)}]

                status, resp = lists.add_merge_field_to_db(list_id, merge_id, tag, name, type, required, public, display_order, default_value, options)
                if not status:
                    return False, "Error", [{'Message': resp}]
                return True, "OK", resp
            elif method == "post":
                status, response = lists.add_merge_field(brand, list_id, tag, name, type, required, public, display_order, default_value, options)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == 'get_single':
                status, response = lists.get_single_merge_field(id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == "patch":
                if 'old_tag' not in request_object:
                    return False, "Error", [{'Message': 'old_tag not specified'}]
                old_tag = request_object['old_tag']
                status, response = lists.update_merge_field(brand, list_id, old_tag, tag, name, type, required, public, display_order, default_value, options, merge_id, id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == "delete":
                status, response = lists.delete_merge_field(brand, list_id, merge_id, id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "list_activity":
            if method == "post":
                if 'list_id' not in request_object:
                	return False, "Error", [{'Message': 'list_id not specified'}]
                list_id = request_object['list_id']
                if 'day' not in request_object:
                	return False, "Error", [{'Message': 'day not specified'}]
                day = request_object['day']
                emails_sent = 0
                if 'emails_sent' in request_object:
                	emails_sent = request_object['emails_sent']
                unique_opens = 0
                if 'unique_opens' in request_object:
                	unique_opens = request_object['unique_opens']
                recipient_clicks = 0
                if 'recipient_clicks' in request_object:
                	recipient_clicks = request_object['recipient_clicks']
                hard_bounce = 0
                if 'hard_bounce' in request_object:
                	hard_bounce = request_object['hard_bounce']
                soft_bounce = 0
                if 'soft_bounce' in request_object:
                	soft_bounce = request_object['soft_bounce']
                subs = 0
                if 'subs' in request_object:
                	subs = request_object['subs']
                unsubs = 0
                if 'unsubs' in request_object:
                	unsubs = request_object['unsubs']
                other_adds = 0
                if 'other_adds' in request_object:
                	other_adds = request_object['other_adds']
                other_removes = 0
                if 'other_removes' in request_object:
                	other_removes = request_object['other_removes']
                status, response = lists.post_activity(brand, list_id, day, emails_sent, unique_opens, recipient_clicks, hard_bounce, soft_bounce, subs, unsubs, other_adds, other_removes, g.user)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", f._obj_to_dict([response])
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "subscriber_activity":
            if method == "post":
                if 'list_subscriber_id' not in request_object:
                	return False, "Error", [{'Message': 'list_subscriber_id not specified'}]
                list_subscriber_id = request_object['list_subscriber_id']
                if 'action' not in request_object:
                	return False, "Error", [{'Message': 'action not specified'}]
                action = request_object['action']
                if 'timestamp' not in request_object:
                	return False, "Error", [{'Message': 'timestamp not specified'}]
                timestamp = request_object['timestamp']
                url = None
                if 'url' in request_object:
                	url = request_object['url']
                type = None
                if 'type' in request_object:
                    type = request_object['type']
                if 'campaign_mailchimp_id' not in request_object:
                	return False, "Error", [{'Message': 'campaign_mailchimp_id not specified'}]
                campaign_mailchimp_id = request_object['campaign_mailchimp_id']
                if 'title' not in request_object:
                	return False, "Error", [{'Message': 'title not specified'}]
                title = request_object['title']
                status, response = lists.post_subscriber_activity(brand, list_subscriber_id, action, timestamp, url, type, campaign_mailchimp_id, title, g.user)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", f._obj_to_dict([response])
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "subscribers":
            if method != 'search' and 'list_id' not in request_object:
                return False, "Error", [{'Message': 'List ID not specified'}]
            elif 'list_id' in request_object:
                list_id = request_object['list_id']
            if method == "add":
                if 'email_id' not in request_object:
                	return False, "Error", [{'Message': 'email_id not specified'}]
                email_id = request_object['email_id']
                if 'email_address' not in request_object:
                	return False, "Error", [{'Message': 'email_address not specified'}]
                email_address = request_object['email_address']
                if 'unique_email_id' not in request_object:
                	return False, "Error", [{'Message': 'unique_email_id not specified'}]
                unique_email_id = request_object['unique_email_id']
                if 'email_type' not in request_object:
                	return False, "Error", [{'Message': 'email_type not specified'}]
                email_type = request_object['email_type']
                if 'status' not in request_object:
                	return False, "Error", [{'Message': 'status not specified'}]
                status = request_object['status']
                timestamp_signup = None
                if 'timestamp_signup' in request_object:
                    timestamp_signup = request_object['timestamp_signup']
                last_changed = None
                if 'last_changed' in request_object:
                    last_changed = request_object['last_changed']
                location = {}
                if 'location' in request_object:
                    try:
                        location = json.loads(request_object['location'])
                    except:
                        pass
                merge_fields = None
                if 'merge_fields' in request_object:
                    try:
                        merge_fields = json.loads(request_object['merge_fields'])
                    except Exception as e:
                        return False, "Error", [{'Message': 'merge_fields sent but cannot be translated - %s' % str(e)}]

                status, results = lists.add_subscriber_to_db(brand, list_id, email_id, email_address, unique_email_id, email_type, status,timestamp_signup, last_changed, location, merge_fields, g.user)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
            elif method == "get":
                if 'page' not in request_object:
                    return False, "Error", [{'Message': 'page not specified'}]
                
                if 'limit' not in request_object:
                    return False, "Error", [{'Message': 'limit not specified'}]
                try:
                    limit = int(request_object['limit'])
                    page = int(request_object['page'])
                    status, results = lists.get_subscribers(list_id, page, limit)
                    if not status:
                        return False, "Error", [{'Message': results}]
                    return True, "OK", results
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            elif method == "delete":
                if 'subscriber[]' not in request_object:
                    return False, "Error", [{'Message':'No subscribers specified'}]

                status, response = lists.delete_subscribers(brand, request_object['subscriber[]'])
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == "search":
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                if 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                search_list_id = request_object['search_folder_id']

                status, results = lists.search_subscribers(search_for, search_contains, search_list_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "folders":
            if method == "new":
                if 'name' not in request_object:
                    return False, "Error", [{"Message": "Request missing name"}]
                elif 'folder_type' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_type'}]
                parent_id = None
                if 'parent_id' in request_object:
                    parent_id = request_object['parent_id']
                name = request_object['name']
                folder_type = request_object['folder_type']
                status, resp = folders.create_folder(brand, name, parent_id, folder_type)
                if status:
                    return True, "OK", {"ID": resp.id}
                else:
                    return False, "Error", [{'Message': resp}]
            if method == "rename":
                if 'name' not in request_object:
                    return False, "Error", [{"Message": "Request missing name"}]
                elif 'folder_id' not in request_object:
                    return False, "Error", [{'Message': "Request missing folder_id"}]

                name = request_object['name']
                folder_id = request_object['folder_id']
                status, resp = folders.rename_folder(brand, folder_id, name)
                if status:
                    return True, "OK", {"ID": resp.id}
                else:
                    return False, "Error", [{'Message': resp}]
            elif method == "delete":
                if 'folder_id' not in request_object:
                    return False, "Error", [{"Message": "Request missing folder_id"}]
                folder_id = request_object['folder_id']
                status, resp = folders.delete_folder(brand, folder_id)
                if status:
                    return True, "OK", ""
                else:
                    return False, "Error", [{'Message': resp}]
            elif method == "get":
                folder_id = None
                folder_type = None
                if 'folder_id' in request_object:
                    folder_id = request_object['folder_id']
                if folder_type in request_object:
                    folder_type = request_object['folder_type']
                status, resp = folders.get_folders(brand, folder_id, folder_type)
                if status:
                    return True, "OK", resp
                else:
                    return False, "Error", [{'Message': resp}]
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "imports":
            if method == "files":
                try:
                    files = activities.get_import_folders(brand)
                    return True, "OK", files
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            if method == "mapping":
                if 'target_type' not in request_object:
                    return False, "Error", [{'Message': 'Target type not specified'}]
                if 'target_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Target folder ID not specified'}]
                elif 'import_file' not in request_object:
                    return False, "Error", [{'Message': 'Import file not specified'}]
                elif 'import_file_delimiter' not in request_object:
                    return False, "Error", [{'Message': "Import file delimiter not specified"}]
                target_type = request_object['target_type']
                import_file = request_object['import_file']
                import_file_delimiter = request_object['import_file_delimiter']
                target_folder_id = request_object['target_folder_id']
                try:
                    status, header, fields = activities.setup_import_mapping(brand, target_folder_id, target_type, import_file, import_file_delimiter)
                    if status:
                        return True, "OK", {'FileHeader': header, 'ImportFields':fields }
                    else:
                        return False, "Error", [{'Message': header}]
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            if method == "submit":
                if 'name' not in request_object:
                    return False, "Error", [{'Message': 'Name not specified'}]
                if 'target_type' not in request_object:
                    return False, "Error", [{'Message': 'Target type not specified'}]
                elif 'import_file' not in request_object:
                    return False, "Error", [{'Message': 'Import file not specified'}]
                elif 'import_file_delimiter' not in request_object:
                    return False, "Error", [{'Message': "Import file delimiter not specified"}]
                elif 'import_type' not in request_object:
                    return False, "Error", [{'Message': 'Import type not specified'}]
                elif 'target_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Target folder not specified'}]
                elif 'mapping[]' not in request_object:
                    return False, "Error", [{'Message': 'Mappings not specified'}]
                name = request_object['name']
                target_type = request_object['target_type']
                import_file = request_object['import_file']
                import_file_delimiter = request_object['import_file_delimiter']
                import_type = request_object['import_type']
                target_folder_id = request_object['target_folder_id']
                mappings = request_object['mapping[]']
                import_notification = ""
                if 'import_notification' in request_object:
                    import_notification = request_object['import_notification']
                folder_id = ""
                if 'folder_id' in request_object:
                    folder_id = request_object['folder_id']
                system_def = False
                if 'system' in request_object:
                    system_def = True
                try:
                    status, res = activities.api_submit_import(brand, name, folder_id, target_type, target_folder_id, import_file, import_file_delimiter, import_type, import_notification, mappings, g.user, system_def)
                    if status:
                        return True, "OK", res
                    else:
                        return False, "Error", [{'Message': res}]
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "exports":
            if method == "fields":
                if 'target_type' not in request_object:
                    return False, "Error", [{'Message': 'Target type not specified'}]
                target_type = request_object['target_type']
                if 'target_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'target_folder_id not specified'}]
                target_folder_id = request_object['target_folder_id']
                try:
                    if 'subscribers' not in target_type:
                        return True, "OK", forms.get_export_fields(target_type)
                    else:
                        if target_type == 'subscribers':
                            status, results = lists.get_subscriber_export_fields(brand, target_folder_id)
                        elif target_type == 'segment_subscribers':
                            status, results = segments.get_subscriber_export_fields(brand, target_folder_id)
                        else:
                            return False, "Error", [{'Message': 'Export fields for type "%s" unavailable' % target_type}]
                        if not status:
                            return False, "Error", [{'Message': results}]
                        return True, "OK", results
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            if method == "submit":
                if 'name' not in request_object:
                    return False, "Error", [{'Message': 'Name not specified'}]
                if 'target_type' not in request_object:
                    return False, "Error", [{'Message': 'Target type not specified'}]
                elif 'export_file' not in request_object:
                    return False, "Error", [{'Message': 'Import file not specified'}]
                elif 'export_file_delimiter' not in request_object:
                    return False, "Error", [{'Message': "Import file delimiter not specified"}]
                elif 'export_type' not in request_object:
                    return False, "Error", [{'Message': 'Import type not specified'}]
                elif 'target_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Target folder not specified'}]
                elif 'field[]' not in request_object:
                    return False, "Error", [{'Message': 'Mappings not specified'}]
                name = request_object['name']
                target_type = request_object['target_type']
                export_file = request_object['export_file']
                export_file_delimiter = request_object['export_file_delimiter']
                export_type = request_object['export_type']
                target_folder_id = request_object['target_folder_id']
                fields = request_object['field[]']
                export_notification = ""
                if 'export_notification' in request_object:
                    export_notification = request_object['export_notification']
                folder_id = ""
                if 'folder_id' in request_object:
                    folder_id = request_object['folder_id']
                system_def = False
                if 'system' in request_object:
                    system_def = True
                target_objects = []
                if 'selected_object[]' in request_object:
                    target_objects = request_object['selected_object[]']

                try:
                    status, res = activities.api_submit_export(brand, name, folder_id, target_type, target_folder_id, export_file, export_file_delimiter, export_type, export_notification, fields, target_objects, g.user, system_def)
                    if status:
                        return True, "OK", res
                    else:
                        return False, "Error", [{'Message': res}]
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "forms":
            if method == 'search':
                if 'target_type' not in request_object:
                    return False, "Error", [{'Message': 'Target type not specified'}]
                target_type = request_object['target_type']
                try:
                    if target_type.endswith("subscribers"):
                        if 'target_list_id' not in request_object:
                            return False, "Error", [{'Message': 'Target List not specified'}]
                        target_list_id = request_object['target_list_id']
                        if target_type.startswith('segment'):
                            status, fields = segments.get_subscriber_search_fields(brand, target_list_id)
                        else:
                            status, fields = lists.get_subscriber_search_fields(target_list_id)
                        if not status:
                            return False, "Error", [{'Message': fields}]
                    else:
                        fields = forms.get_search_fields(target_type)
                    return True, "OK", fields
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "templates":
            if method in ('post', 'patch'):
                if 'category_id' not in request_object:
                    return False, "Error", [{'Message': 'category_id not specified'}]
                category_id = request_object['category_id']
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'folder_id not specified'}]
                folder_id = request_object['folder_id']
                if 'mailchimp_id' not in request_object:
                    return False, "Error", [{'Message': 'mailchimp_id not specified'}]
                mailchimp_id = request_object['mailchimp_id']
                if 'name' not in request_object:
                    return False, "Error", [{'Message': 'name not specified'}]
                name = request_object['name']
                if 'type' not in request_object:
                    return False, "Error", [{'Message': 'type not specified'}]
                type = request_object['type']
                if 'active' not in request_object:
                    return False, "Error", [{'Message': 'active not specified'}]
                active = request_object['active']
                if 'thumbnail' not in request_object:
                    return False, "Error", [{'Message': 'thumbnail not specified'}]
                thumbnail = request_object['thumbnail']
                sections = None
                if 'sections' in request_object:
                    try:
                        sections = json.loads(request_object['sections'])
                    except:
                        pass
                html = ""
                if 'html' in request_object:
                    html = request_object['html']
            if method == "post":
                status, response = templates.add_template_to_db(brand, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, g.user, html, sections)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == 'move':
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = templates.move_template(brand, id, folder_id, g.user)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "savehtml":
                if 'template_id' not in request_object:
                    return False, "Error", [{'Message': 'template_id not specified'}]
                template_id = request_object['template_id']
                if 'content' not in request_object:
                    return False, "Error", [{'Message': 'content not specified'}]
                content = request_object['content']

                status, response = templates.save_html(brand, template_id, content, g.user)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == 'delete':
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = templates.delete_template(brand, id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "template_categories":
            if method in('add', 'get_by_name'):
                if 'name' not in request_object:
                    return False, "Error", [{'Message': 'name not specified'}]
                name = request_object['name']
            if method == "add":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'folder_id not specified'}]
                folder_id = request_object['folder_id']
                status, response = templates.add_template_category(brand, name, folder_id, g.user.id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == "get_by_name":
                status, response = templates.get_template_category_by_name(brand, name)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == "move":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = templates.move_category(id, folder_id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "delete":
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = templates.delete_category(brand, id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            elif method == "search":
                if 'search_type' not in request_object:
                    return False, "Error", [{'Message': 'search_type not specified'}]
                search_type = request_object['search_type']
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                search_folder_id = None
                if search_type == '2' and 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                elif search_type == '2':
                    search_folder_id = request_object['search_folder_id']

                #try:
                status, results = templates.search_categories(brand, search_type, search_for, search_contains, search_folder_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
                #except Exception as e:
                #    return False, "Error", [{'Message': str(e)}]
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "system_merge_fields":
            if method == "post":
                if 'name' not in request_object:
                    return False, "Error", [{'Message': 'name not specified'}]
                name = request_object['name']
                if 'tag' not in request_object:
                    return False, "Error", [{'Message': 'tag not specified'}]
                tag = request_object['tag']
                description = ""
                if 'description' in request_object:
                    description = request_object['description']

                status, response = system.system_merge_field_to_db(name, tag, description, g.user)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == 'emails':
            if method == 'get':
                if 'id' not in request_object:
                    return False, "Error", [{'Message': 'id not specified'}]
                email_id = request_object['id']
                status, response = emails.email_by_id(brand, email_id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", f._obj_to_dict([response])
            elif method == 'post':
                if 'template_id' not in request_object:
                	return False, "Error", [{'Message': 'template_id not specified'}]
                template_id = request_object['template_id']
                if 'name' not in request_object:
                	return False, "Error", [{'Message': 'name not specified'}]
                name = request_object['name']
                if 'subject_line' not in request_object:
                	return False, "Error", [{'Message': 'subject_line not specified'}]
                subject_line = request_object['subject_line']
                
                if 'folder_id' in request_object:
                    folder_id = request_object['folder_id']
                else:
                    folder = folders.get_root_folder(brand, "emails")
                    folder_id = folder.id
                last_sent = None
                if 'last_sent' in request_object:
                	last_sent = request_object['last_sent']
                html = ""
                if 'html' in request_object:
                	html = request_object['html']

                status, response = emails.email_to_db(brand, template_id, name, subject_line, folder_id, g.user, last_sent, html)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == 'savehtml':
                if 'email_id' not in request_object:
                    return False, "Error", [{'Message': 'Email ID not specified'}]
                email_id = request_object['email_id']
                content = ""
                sections = []
                if 'content' in request_object:
                    content = request_object['content']
                if 'section[]' in request_object:
                    sections = request_object['section[]']

                status, response = emails.save_html(brand, email_id, content, sections, g.user)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == "search":
                if 'search_type' not in request_object:
                    return False, "Error", [{'Message': 'search_type not specified'}]
                search_type = request_object['search_type']
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                search_folder_id = None
                if search_type == '2' and 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                elif search_type == '2':
                    search_folder_id = request_object['search_folder_id']
                status, results = emails.search(brand, search_type, search_for, search_contains, search_folder_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
            elif method == "move":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = emails.move(brand, id, folder_id, g.user)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "delete":
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = emails.delete(brand, id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == "segments":
            if method == 'post':
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'folder_id not specified'}]
                folder_id = request_object['folder_id']
                if 'mailchimp_id' not in request_object:
                	return False, "Error", [{'Message': 'mailchimp_id not specified'}]
                mailchimp_id = request_object['mailchimp_id']
                if 'name' not in request_object:
                	return False, "Error", [{'Message': 'name not specified'}]
                name = request_object['name']
                if 'match' not in request_object:
                	return False, "Error", [{'Message': 'match not specified'}]
                match = request_object['match']
                if 'type' not in request_object:
                	return False, "Error", [{'Message': 'type not specified'}]
                type = request_object['type']
                if 'list_id' not in request_object and 'list_mailchimp_id' not in request_object:
                    return False, "Error", [{'Message': 'List ID or Mailchimp ID not specified'}]
                list_id = None
                list_mailchimp_id = None
                if 'list_id' in request_object:
                    list_id = request_object['list_id']
                if 'list_mailchimp_id' in request_object:
                    list_mailchimp_id = request_object['list_mailchimp_id']
                conditions = []
                if 'conditions' in request_object:
                    try:
                        conditions = json.loads(request_object['conditions'])
                        if not isinstance(conditions, list):
                            return False, "Error", [{'Message': 'conditions must be of type list'}]
                    except Exception as ex:
                        return False, "Error", [{'Message': str(ex)}]

                status, response = segments.segment_to_db(brand, folder_id, mailchimp_id, name, type, match, g.user, conditions=conditions, list_id=list_id, list_mailchimp_id=list_mailchimp_id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == 'all':
                if 'list_id' not in request_object:
                    return False, "Error", [{'Message': 'list_id not specified'}]
                list_id = request_object['list_id']
                return True, "OK", segments.all_segments(brand, list_id)
            elif method == "get_subscribers":
                if 'page' not in request_object:
                    return False, "Error", [{'Message': 'page not specified'}]
                if 'limit' not in request_object:
                    return False, "Error", [{'Message': 'limit not specified'}]
                if 'segment_id' not in request_object:
                    return False, "Error", [{'Message': 'segment_id not specified'}]
                try:
                    limit = int(request_object['limit'])
                    page = int(request_object['page'])
                    segment_id = request_object['segment_id']
                    status, results = segments.get_subscribers(brand, segment_id, page, limit)
                    if not status:
                        return False, "Error", [{'Message': results}]
                    return True, "OK", results
                except Exception as e:
                    return False, "Error", [{'Message': str(e)}]
            elif method == "move":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = segments.move_segment(brand, id, folder_id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "search":
                if 'search_type' not in request_object:
                    return False, "Error", [{'Message': 'search_type not specified'}]
                search_type = request_object['search_type']
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                search_folder_id = None
                if search_type == '2' and 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                elif search_type == '2':
                    search_folder_id = request_object['search_folder_id']

                #try:
                status, results = segments.search(brand, search_type, search_for, search_contains, search_folder_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
                #except Exception as e:
                #    return False, "Error", [{'Message': str(e)}]
            elif method == "delete":
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = segments.delete_segment(brand, id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == 'segment_subscribers':
            if method == "search":
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                if 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                search_segment_id = request_object['search_folder_id']

                status, results = segments.search_subscribers(brand, search_for, search_contains, search_segment_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
            elif method == 'remove':
                if 'segment_id' not in request_object:
                    return False, "Error", [{'Message': 'segment_id not specified'}]
                segment_id = request_object['segment_id']
                if 'subscriber[]' not in request_object:
                    return False, "Error", [{'Message': 'No subscribers specified'}]
                subscribers = request_object['subscriber[]']
                status, response = segments.remove_subscribers(brand, segment_id, subscribers)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            elif method == 'refresh':
                if 'segment_id' not in request_object:
                    return False, "Error", [{'Message': 'segment_id not specified'}]
                segment_id = request_object['segment_id']

                status, response = segments.apply_segment_subscribers_from_mailchimp(brand, segment_id)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action == 'campaigns':
            if method == 'post':
                if 'mailchimp_id' not in request_object:
                    return False, "Error", [{'Message': 'mailchimp_id not specified'}]
                mailchimp_id = request_object['mailchimp_id']
                if 'brand' not in request_object:
                    return False, "Error", [{'Message': 'brand not specified'}]
                brand = request_object['brand']
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'folder_id not specified'}]
                folder_id = request_object['folder_id']
                if 'name' not in request_object:
                    return False, "Error", [{'Message': 'name not specified'}]
                name = request_object['name']
                if 'type' not in request_object:
                    return False, "Error", [{'Message': 'type not specified'}]
                type = request_object['type']
                if 'status' not in request_object:
                    return False, "Error", [{'Message': 'status not specified'}]
                status = request_object['status']
                if 'emails_sent' not in request_object:
                    return False, "Error", [{'Message': 'emails_sent not specified'}]
                emails_sent = request_object['emails_sent']
                if 'send_time' not in request_object:
                    return False, "Error", [{'Message': 'send_time not specified'}]
                send_time = request_object['send_time']
                if 'created' not in request_object:
                    return False, "Error", [{'Message': 'created not specified'}]
                created = request_object['created']
                if 'content_type' not in request_object:
                    return False, "Error", [{'Message': 'content_type not specified'}]
                content_type = request_object['content_type']
                if 'list_mailchimp_id' not in request_object:
                    return False, "Error", [{'Message': 'list_mailchimp_id not specified'}]
                list_mailchimp_id = request_object['list_mailchimp_id']
                if 'segment_text' not in request_object:
                    return False, "Error", [{'Message': 'segment_text not specified'}]
                segment_text = request_object['segment_text']
                if 'recipient_count' not in request_object:
                    return False, "Error", [{'Message': 'recipient_count not specified'}]
                recipient_count = request_object['recipient_count']
                saved_segment_id = None
                if 'saved_segment_id' in request_object:
                    saved_segment_id = request_object['saved_segment_id']
                if 'subject_line' not in request_object:
                    return False, "Error", [{'Message': 'subject_line not specified'}]
                subject_line = request_object['subject_line']
                if 'from_name' not in request_object:
                    return False, "Error", [{'Message': 'from_name not specified'}]
                from_name = request_object['from_name']
                if 'reply_to' not in request_object:
                    return False, "Error", [{'Message': 'reply_to not specified'}]
                reply_to = request_object['reply_to']
                if 'authenticate' not in request_object:
                    return False, "Error", [{'Message': 'authenticate not specified'}]
                authenticate = request_object['authenticate']
                if 'auto_footer' not in request_object:
                    return False, "Error", [{'Message': 'auto_footer not specified'}]
                auto_footer = request_object['auto_footer']
                if 'inline_css' not in request_object:
                    return False, "Error", [{'Message': 'inline_css not specified'}]
                inline_css = request_object['inline_css']
                if 'template_id' not in request_object:
                    return False, "Error", [{'Message': 'template_id not specified'}]
                template_id = request_object['template_id']
                if 'track_opens' not in request_object:
                    return False, "Error", [{'Message': 'track_opens not specified'}]
                track_opens = request_object['track_opens']
                if 'track_clicks' not in request_object:
                    return False, "Error", [{'Message': 'track_clicks not specified'}]
                track_clicks = request_object['track_clicks']
                if 'delivery_status_enabled' not in request_object:
                    return False, "Error", [{'Message': 'delivery_status_enabled not specified'}]
                delivery_status_enabled = request_object['delivery_status_enabled']
                can_cancel = None
                delivery_status = None
                ds_emails_sent = None
                ds_emails_canceled = None
                if delivery_status_enabled == True:
                    if 'can_cancel' not in request_object:
                        return False, "Error", [{'Message': 'can_cancel not specified'}]
                    can_cancel = request_object['can_cancel']
                    if 'delivery_status' not in request_object:
                        return False, "Error", [{'Message': 'delivery_status not specified'}]
                    delivery_status = request_object['delivery_status']
                    if 'ds_emails_sent' not in request_object:
                        return False, "Error", [{'Message': 'ds_emails_sent not specified'}]
                    ds_emails_sent = request_object['ds_emails_sent']
                    if 'ds_emails_canceled' not in request_object:
                        return False, "Error", [{'Message': 'ds_emails_canceled not specified'}]
                    ds_emails_canceled = request_object['ds_emails_canceled']
                status, response = campaigns.post_campaign_to_db(mailchimp_id, brand, folder_id, name, type, status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled, g.user)
                if not status:
                    return False, "Error", [{'Message': str(response)}]
                return True, "OK", response
            elif method == "move":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = campaigns.move_campaign(brand, id, folder_id, g.user)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "search":
                if 'search_type' not in request_object:
                    return False, "Error", [{'Message': 'search_type not specified'}]
                search_type = request_object['search_type']
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                search_folder_id = None
                if search_type == '2' and 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                elif search_type == '2':
                    search_folder_id = request_object['search_folder_id']

                #try:
                status, results = campaigns.search(brand, search_type, search_for, search_contains, search_folder_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
                #except Exception as e:
                #    return False, "Error", [{'Message': str(e)}]
            elif method == "delete":
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = campaigns.delete_campaign(brand, id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action in ("ab_tests", "variates", "varient_campaigns"):
            if method == "move":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = campaigns.move_variate(brand, id, folder_id, g.user)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "search":
                if 'search_type' not in request_object:
                    return False, "Error", [{'Message': 'search_type not specified'}]
                search_type = request_object['search_type']
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                search_folder_id = None
                if search_type == '2' and 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                elif search_type == '2':
                    search_folder_id = request_object['search_folder_id']

                #try:
                status, results = campaigns.search_variate_campaigns(brand, search_type, search_for, search_contains, search_folder_id)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
                #except Exception as e:
                #    return False, "Error", [{'Message': str(e)}]
            elif method == "delete":
                if 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                ids = request_object['id[]']
                for id in ids:
                    status, resp = campaigns.delete_variate(brand, id)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", ""
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        elif action in ('campaign_tracking', 'ab_test_tracking', 'rtm_tracking'):
            if method == "move":
                if 'folder_id' not in request_object:
                    return False, "Error", [{'Message': 'Request missing folder_id'}]
                elif 'id[]' not in request_object:
                    return False, "Error", [{'Message': 'Request missing ids'}]
                folder_id = request_object['folder_id']
                ids = request_object['id[]']
                for id in ids:
                    status, resp = tracking.move(brand, id, folder_id, g.user)
                    if not status:
                        return False, "Error", [{'Message': resp}]
                return True, "OK", {'ID': folder_id}
            elif method == "search":
                if 'search_type' not in request_object:
                    return False, "Error", [{'Message': 'search_type not specified'}]
                search_type = request_object['search_type']
                if 'search_for' not in request_object:
                    return False, "Error", [{'Message': 'search_for not specified'}]
                search_for = request_object['search_for']
                if 'search_contains' not in request_object:
                    return False, "Error", [{'Message': 'search_contains not specified'}]
                search_contains = request_object['search_contains']
                search_folder_id = None
                if search_type == '2' and 'search_folder_id' not in request_object:
                    return False, "Error", [{'Message': 'search_folder_id not specified'}]
                elif search_type == '2':
                    search_folder_id = request_object['search_folder_id']

                #try:
                status, results = tracking.search(brand, search_type, search_for, search_contains, search_folder_id, action)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
                #except Exception as e:
                #    return False, "Error", [{'Message': str(e)}]
            elif method == 'export':
                if 'name' not in request_object:
                    return False, "Error", [{'Message': 'name not specified'}]
                name = request_object['name']
                if 'target_type' not in request_object:
                    return False, "Error", [{'Message': 'target_type not specified'}]
                target_type = request_object['target_type']
                if 'target_activity' not in request_object:
                    return False, "Error", [{'Message': 'target_activity not specified'}]
                target_activity = request_object['target_activity']
                if 'target_id' not in request_object:
                    return False, "Error", [{'Message': 'target_id not specified'}]
                target_id = request_object['target_id']
                if 'export_file' not in request_object:
                    return False, "Error", [{'Message': 'export_file not specified'}]
                export_file = request_object['export_file']
                if 'export_file_delimiter' not in request_object:
                    return False, "Error", [{'Message': 'export_file_delimiter not specified'}]
                export_file_delimiter = request_object['export_file_delimiter']
                export_notification = ""
                if 'export_notification' in request_object:
                    export_notification = request_object['export_notification']
                folder_id = ""
                if 'folder_id' in request_object:
                    folder_id = request_object['folder_id']
                system_def = False
                if 'system' in request_object:
                    system_def = True

                status, results = activities.api_submit_tracking_export(brand, name, folder_id, target_type, target_activity, target_id, export_file, export_file_delimiter, export_notification, g.user, system_def)
                if not status:
                    return False, "Error", [{'Message': results}]
                return True, "OK", results
            elif method == 'search_activity':
                if 'tracking_id' not in request_object:
                    return False, "Error", [{'Message': 'tracking_id not specified'}]
                tracking_id = request_object['tracking_id']
                if 'target_activity' not in request_object:
                    return False, "Error", [{'Message': 'target_activity not specified'}]
                target_activity = request_object['target_activity']
                if 'target_type' not in request_object:
                    return False, "Error", [{'Message': 'target_type not specified'}]
                target_type = request_object['target_type']
                if 'contains' not in request_object:
                    return False, "Error", [{'Message': 'contains not specified'}]
                contains = request_object['contains']

                status, response = tracking.search_tracking_detail(brand, tracking_id, target_activity, target_type, contains)
                if not status:
                    return False, "Error", [{'Message': response}]
                return True, "OK", response
            else:
                status = False
                status_type = "Error"
                results = [{'Message': 'Method "%s" for action "%s" not defined' % (method, action)}]
        else:
            status = False
            status_type = "Error"
            results = [{'Message': 'Action "%s" not defined' % (action)}]
    else:
        status = False
        status_type = "Error"
        results = [{'Message': 'Brand MID not present in request'}]

    return status, status_type, results

