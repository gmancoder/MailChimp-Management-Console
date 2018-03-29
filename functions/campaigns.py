#!/usr/bin/env python
from models.shared import db
from models.emails import *
from models.folders import *
from models.forms import *
from models.users import *
from models.campaigns import *
import activities
import core as f
import forms
import json
import datetime
import folders
import templates
import unidecode
import segments
import lists
import emails
from sqlalchemy import *
from sqlalchemy import func

def campaign():
    fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'Name', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'email_id': {'Label': 'Email', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 2,
        }},
    'list_id': {'Label': 'List', 'Required': True, 'Form': {
        'Group': {'Name': 'Audience', 'Rank': 2},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 1,
        }},
    'segment_id': {'Label': 'Segment', 'Required': True, 'Form': {
        'Group': {'Name': 'Audience', 'Rank': 2},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 2,
        }},
    'subject_line': {'Label': 'Subject Line', 'Required': True, 'Form': {
        'Group': {'Name': 'Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'from_name': {'Label': 'From Name', 'Required': True, 'Form': {
        'Group': {'Name': 'Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 2,
        }},
    'reply_to': {'Label': 'Reply To', 'Required': True, 'Form': {
        'Group': {'Name': 'Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'email',
        'MaxLength': 200,
        'Rank': 3,
        }},
    'auto_footer': {'Label': 'Append Default Footer', 'Required': True, 'Form': {
        'Group': {'Name': 'Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'checkbox',
        'Rank': 4,
        }},
    'inline_css': {'Label': 'Automatically In-Line CSS', 'Required': True, 'Form': {
        'Group': {'Name': 'Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'checkbox',
        'Rank': 5,
        }},
    'track_opens': {'Label': 'Track Opens', 'Required': True, 'Form': {
        'Group': {'Name': 'Tracking', 'Rank': 4},
        'Field': 'input',
        'Type': 'checkbox',
        'Rank': 1,
        }},
    'track_clicks': {'Label': 'Track Clicks', 'Required': True, 'Form': {
        'Group': {'Name': 'Tracking', 'Rank': 4},
        'Field': 'input',
        'Type': 'checkbox',
        'Rank': 2,
        }},
    }
    return fields

def variate_campaign():
    fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'Name', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'test_type': {'Label': 'Test Type', 'Required': True, 'Form': {
        'Group': {'Name': 'A/B Settings', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {'subject_line': 'Subject Lines', 'from_name': 'From Names', 'content': 'Content', 'send_time': 'Send Times'},
        'Rank': 1,
        }},
    'test_combinations': {'Label': 'Number of Combinations', 'Required': True, 'Form': {
        'Group': {'Name': 'A/B Settings', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {'2': '2', '3': '3'},
        'Rank': 2,
        }},
    'test_size': {'Label': 'Test Size', 'Required': True, 'Form': {
        'Group': {'Name': 'A/B Settings', 'Rank': 1},
        'Field': 'input',
        'Type': 'number',
        'Rank': 3,
        }},
    'winning_criteria': {'Label': 'Winning Criteria', 'Required': True, 'Form': {
        'Group': {'Name': 'A/B Settings', 'Rank': 1},
        'Field': 'select',
        'Type': 'select',
        'Options': {'opens': 'Opens', 'clicks': 'Clicks'},
        'Rank': 4,
        }},
    'wait_time': {'Label': 'Hours before winner', 'Required': True, 'Form': {
        'Group': {'Name': 'A/B Settings', 'Rank': 1},
        'Field': 'input',
        'Type': 'number',
        'Rank': 5,
        }},
    'list_id': {'Label': 'List', 'Required': True, 'Form': {
        'Group': {'Name': 'Audience', 'Rank': 2},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 1,
        }},
    'segment_id': {'Label': 'Segment', 'Required': True, 'Form': {
        'Group': {'Name': 'Audience', 'Rank': 2},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 2,
        }},
    'subject_line': {'Label': 'Subject Line', 'Required': True, 'Form': {
        'Group': {'Name': 'Default Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'from_name': {'Label': 'From Name', 'Required': True, 'Form': {
        'Group': {'Name': 'Default Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 2,
        }},
    'reply_to': {'Label': 'Reply To', 'Required': True, 'Form': {
        'Group': {'Name': 'Default Send Settings', 'Rank': 3},
        'Field': 'input',
        'Type': 'email',
        'MaxLength': 200,
        'Rank': 3,
        }},
    'email_id_1': {'Label': 'Email', 'Required': True, 'Form': {
        'Group': {'Name': 'Test Combination 1', 'Rank': 4},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 1,
        }},
    'send_date_1': {'Label': 'Send Date', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 1', 'Rank': 4},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 10,
        'Rank': 2,
        }},
    'send_time_1': {'Label': 'Send Time', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 1', 'Rank': 4},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 2,
        }},
    'subject_line_1': {'Label': 'Subject Line', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 1', 'Rank': 4},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'from_name_1': {'Label': 'From Name', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 1', 'Rank': 4},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 2,
        }},
    'reply_to_1': {'Label': 'Reply To', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 1', 'Rank': 4},
        'Field': 'input',
        'Type': 'email',
        'MaxLength': 200,
        'Rank': 3,
        }},
    'email_id_2': {'Label': 'Email', 'Required': True, 'Form': {
        'Group': {'Name': 'Test Combination 2', 'Rank': 5},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 1,
        }},
    'send_date_2': {'Label': 'Send Date', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 2', 'Rank': 5},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 10,
        'Rank': 2,
        }},
    'send_time_2': {'Label': 'Send Time', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 2', 'Rank': 5},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 2,
        }},
    'subject_line_2': {'Label': 'Subject Line', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 2', 'Rank': 5},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'from_name_2': {'Label': 'From Name', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 2', 'Rank': 5},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 2,
        }},
    'reply_to_2': {'Label': 'Reply To', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 2', 'Rank': 5},
        'Field': 'input',
        'Type': 'email',
        'MaxLength': 200,
        'Rank': 3,
        }},
    'email_id_3': {'Label': 'Email', 'Required': True, 'Form': {
        'Group': {'Name': 'Test Combination 3', 'Rank': 6},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 1,
        }},
    'send_date_3': {'Label': 'Send Date', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 3', 'Rank': 6},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 10,
        'Rank': 2,
        }},
    'send_time_3': {'Label': 'Send Time', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 3', 'Rank': 6},
        'Field': 'select',
        'Type': 'select',
        'Options': {},
        'Rank': 2,
        }},
    'subject_line_3': {'Label': 'Subject Line', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 3', 'Rank': 6},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'from_name_3': {'Label': 'From Name', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 3', 'Rank': 6},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 2,
        }},
    'reply_to_3': {'Label': 'Reply To', 'Required': False, 'Form': {
        'Group': {'Name': 'Test Combination 3', 'Rank': 6},
        'Field': 'input',
        'Type': 'email',
        'MaxLength': 200,
        'Rank': 3,
        }}
    }
    return fields

def all_campaigns(brand_id=None):
    query = Campaign.query
    if brand_id != None:
        query = query.filter(Campaign.brand_id == brand_id)
    return query.all()

def campaign_by_id(brand_id, campaign_id):
    campaign = Campaign.query.filter(and_(Campaign.brand_id == brand_id, Campaign.id == campaign_id)).first()
    if not campaign:
        return False, "Campaign not found"
    return True, campaign

def campaign_by_mailchimp_id(brand_id, campaign_id):
    campaign = Campaign.query.filter(and_(Campaign.brand_id == brand_id, Campaign.mailchimp_id == campaign_id)).first()
    if not campaign:
        return False, "Campaign not found"
    return True, campaign

def campaign_exists_by_name(brand_id, name):
    return Campaign.query.filter(and_(Campaign.brand_id == brand_id, Campaign.name == name)).count() > 0

def campaign_to_form_request(campaign):
    request_object = {}
    request_object['campaigns_email_id'] = str(campaign.email_id)
    request_object['campaigns_segment_id'] = str(campaign.segment_id)
    request_object['campaigns_list_id'] = str(campaign.list_id)
    request_object['campaigns_name'] = campaign.name
    request_object['campaigns_subject_line'] = campaign.subject_line
    request_object['campaigns_from_name'] = campaign.from_name
    request_object['campaigns_reply_to'] = campaign.reply_to
    request_object['campaigns_auto_footer'] = campaign.auto_footer
    request_object['campaigns_inline_css'] = campaign.inline_css
    request_object['campaigns_track_opens'] = campaign.track_opens
    request_object['campaigns_track_clicks'] = campaign.track_clicks
    return request_object

def request_to_campaign(campaign, request_object):
    campaign.email_id = request_object['campaigns_email_id']
    if 'campaigns_segment_id' in request_object and request_object['campaigns_segment_id'] not in ('0', '-'):
        campaign.segment_id = request_object['campaigns_segment_id']
    else:
        campaign.segment_id = None

    campaign.list_id = request_object['campaigns_list_id']
    
    campaign.name = request_object['campaigns_name']
    campaign.subject_line = request_object['campaigns_subject_line']
    campaign.from_name = request_object['campaigns_from_name']
    campaign.reply_to = request_object['campaigns_reply_to']
    if 'campaigns_auto_footer' in request_object:
        campaign.auto_footer = True
    else:
        campaign.auto_footer = False

    if 'campaigns_inline_css' in request_object:
        campaign.inline_css = True
    else:
        campaign.inline_css = False

    if 'campaigns_track_opens' in request_object:
        campaign.track_opens = True
    else:
        campaign.track_opens = False

    if 'campaigns_track_clicks' in request_object:
        campaign.track_clicks = True
    else:
        campaign.track_clicks = False

    return campaign

def post_campaign_to_db(mailchimp_id, brand_id, folder_id, name, type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled, user, sync=False):
    campaign = Campaign()
    status, campaign = campaign_fields_to_obj(campaign, mailchimp_id, brand_id, folder_id, name, type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled)
    if not status:
        return False, campaign
    campaign.created_by = user.id

    try:
        db.session.add(campaign)
        db.session.commit()
        if sync:
            return True, campaign
        return True, f._obj_to_dict([campaign])
    except Exception as ex:
        return False, ex

def campaign_fields_to_obj(campaign, mailchimp_id, brand_id, folder_id, name, type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled):
    campaign.mailchimp_id = mailchimp_id
    campaign.brand_id = brand_id
    if folder_id != None:
        campaign.folder_id = folder_id
    
    # List
    current_list = lists.list_by_mailchimp_id(brand_id, str(list_mailchimp_id))
    if not current_list:
        return False, "List not found"
    campaign.list_id = current_list.id
    campaign.list_name = current_list.name
    
    # Template
    if template_id != None and template_id != "" and template_id != 0:
        status, current_template = templates.template_by_mailchimp_id(brand_id, str(template_id))
        if not status:
            return False, "Template not found"
        campaign.template_id = current_template.id

    # Segment
    if saved_segment_id != None:
        status, current_segment = segments.segment_by_mailchimp_id(brand_id, str(saved_segment_id))
        if not status:
            return False, current_segment
        campaign.segment_id = current_segment.id

    # Email
    if isinstance(name, dict):
        email_name = name['name']
        email_id = name['id']
        status, email = emails.email_by_id(brand_id, email_id)
        if not status:
            return False, "Email not found"
    else:
        email_name = name
        status, email = emails.email_by_campaign_name(brand_id, email_name)
        if not status:
            return False, "Email not found"

    campaign.email_id = email.id
    campaign.name = email_name
    campaign.type = type
    campaign.status = campaign_status
    campaign.emails_sent = emails_sent
    campaign.send_time = send_time
    campaign.created = created
    campaign.content_type = content_type
    campaign.segment_text = segment_text
    campaign.recipient_count = recipient_count
    
    campaign.subject_line = subject_line
    campaign.from_name = from_name
    campaign.reply_to = reply_to
    campaign.authenticate = authenticate
    campaign.auto_footer = auto_footer
    campaign.inline_css = inline_css
    
    campaign.track_opens = track_opens
    campaign.track_clicks = track_clicks
    campaign.delivery_status_enabled = delivery_status_enabled
    if campaign.delivery_status_enabled:
        campaign.can_cancel = can_cancel
        campaign.delivery_status = delivery_status
        campaign.ds_emails_sent = ds_emails_sent
        campaign.ds_emails_canceled = ds_emails_canceled

    return True, campaign

def patch_campaign_to_db(campaign_id, mailchimp_id, brand_id, folder_id, name, type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled, user, sync=True):
    status, campaign = campaign_by_id(brand_id, campaign_id)
    if not status:
        return False, campaign
    
    status, campaign = campaign_fields_to_obj(campaign, mailchimp_id, brand_id, folder_id, name, type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled)
    if not status:
        return False, campaign
    campaign.updated = datetime.datetime.now()
    campaign.updated_by = user.id

    try:
        db.session.commit()
        if sync:
            return True, campaign
        return True, f._obj_to_dict([campaign])
    except Exception as ex:
        return False, ex
def create_mailchimp_object_from_campaign(campaign, campaign_type="regular"):
    mailchimp_obj = {}
    current_list = lists.list_by_id(campaign.brand_id, campaign.list_id)
    if not current_list:
        return False, "List not found"
    mailchimp_obj['type'] = campaign_type
    mailchimp_obj['recipients'] = {'list_id': current_list.mailchimp_id}
    if isinstance(campaign.segment_id, int):
        status, current_segment = segments.segment_by_id(campaign.brand_id, campaign.segment_id)
        if not status:
            return False, current_segment
        mailchimp_obj['recipients']['segment_opts'] = {'saved_segment_id': current_segment.mailchimp_id, 'match': current_segment.match, 'conditions': []}
        for condition in current_segment.conditions.all():
            mailchimp_obj['recipients']['segment_opts']['conditions'].append({'condition_type': condition.type, 'field': condition.field, 'op': condition.op, 'value': condition.value})
    mailchimp_obj['settings'] = {
        'subject_line': campaign.subject_line,
        'title': campaign.name,
        'from_name': campaign.from_name,
        'reply_to': campaign.reply_to,
        'auto_footer': False,
        'inline_css': False
    }
    if campaign_type == 'regular':
        mailchimp_obj['settings']['auto_footer'] = campaign.auto_footer
        mailchimp_obj['settings']['inline_css'] = campaign.inline_css
    status, current_folder = folders.get_folder_by_id(campaign.brand_id, campaign.folder_id)
    if not status:
        return False, current_folder
    mailchimp_obj['settings']['folder_id'] = current_folder.mailchimp_id
    if campaign_type == 'regular':
        mailchimp_obj['tracking'] = {
            'opens': campaign.track_opens,
            'html_clicks': campaign.track_clicks,
            'text_clicks': campaign.track_clicks
        }
    else:
        mailchimp_obj['tracking'] = {
            'opens': True,
            'html_clicks': True,
            'text_clicks': True
        }

    if campaign_type == 'variate':
        mailchimp_obj['variate_settings'] = {
            'winner_criteria': campaign.winner_criteria,
            'wait_time': int(campaign.wait_time) * 60,
            'test_size': int(campaign.test_size),
        }
        subject_lines = []
        send_times = []
        from_names = []
        reply_to_addresses = []
        for combo in campaign.combinations:
            if combo.subject_line != None and campaign.test_type == 'subject_line':
                subject_lines.append(combo.subject_line)
            if combo.send_time != None and campaign.test_type == 'send_time':
                send_times.append(combo.send_time)
            if combo.from_name != None and campaign.test_type == 'from_name':
                from_names.append(combo.from_name)
                if combo.reply_to != None:
                    reply_to_addresses.append(combo.reply_to)
        if len(subject_lines) > 0:
            mailchimp_obj['variate_settings']['subject_lines'] = subject_lines
        elif len(send_times) > 0:
            mailchimp_obj['variate_settings']['send_times'] = send_times
        elif len(from_names) > 0:
            mailchimp_obj['variate_settings']['from_names'] = from_names
            mailchimp_obj['variate_settings']['reply_to_addresses'] = reply_to_addresses
    return True, mailchimp_obj

def campaign_to_mailchimp(campaign, mailchimp_id=None, settings_only=True):
    status, mailchimp_obj = create_mailchimp_object_from_campaign(campaign)
    if not status:
        return False, mailchimp_obj
    brand = f.GetBrandByID(campaign.brand_id)
    
    if mailchimp_id == None:
        status, resp = f.post_to_mailchimp(brand, "campaigns", json.dumps(mailchimp_obj))
    else:
        status, resp = f.patch_to_mailchimp(brand, "campaigns", json.dumps(mailchimp_obj), mailchimp_id)
    print status
    print resp
    if not status:
        return False, resp

    campaign = update_campaign_from_mailchimp_post(campaign, resp)
    if not settings_only:
        status, response = campaign_content_to_mailchimp(campaign)
        if not status:
            return False, response
    return True, campaign

def update_campaign_from_mailchimp_post(campaign, resp):
    j_response = json.loads(resp)
    campaign.mailchimp_id = j_response['id']
    campaign.authenticate = j_response['settings']['authenticate']
    campaign.status = j_response['status']
    campaign.content_type = j_response['content_type']
    campaign.delivery_status_enabled = j_response['delivery_status']['enabled']
    if campaign.delivery_status_enabled:
        campaign.can_cancel = j_response['delivery_status']['can_cancel']
        campaign.delivery_status = j_response['delivery_status']['status']
        campaign.ds_emails_sent = j_response['delivery_status']['emails_sent']
        campaign.ds_emails_canceled = j_response['delivery_status']['emails_canceled']
    return campaign

def campaign_content_to_mailchimp(campaign):
    brand = f.GetBrandByID(campaign.brand_id)
    status, email = emails.email_by_id(campaign.brand_id, campaign.email_id)
    if not status:
        return False, email
    data = {'html': email.full_html}
    return f.post_to_mailchimp(brand, "campaigns/%s/content" % campaign.mailchimp_id, json.dumps(data), "PUT")

def save_campaign(mode, campaign, user):
    try:
        if mode == "new":
            campaign.created_by = user.id
            db.session.add(campaign)
        else:
            campaign.updated = datetime.datetime.now()
            campaign.updated_by = user.id
        db.session.commit()
        return True, campaign
    except Exception as ex:
        return False, str(ex)

def send_email(brand_id, mailchimp_id, test=False, test_emails=[]):
    brand = f.GetBrandByID(brand_id)
    route = 'campaigns/%s/actions/' % mailchimp_id
    data_str = None
    if test:
        route = '%stest' % route
        data = {'test_emails': test_emails, 'send_type': 'html'}
        data_str = json.dumps(data)
    else:
        route = '%ssend' % route

    return f.post_to_mailchimp(brand, route, data_str)

def schedule_campaign(campaign):
    brand = f.GetBrandByID(campaign.brand_id)
    route = 'campaigns/%s/actions/schedule' % campaign.mailchimp_id
    data = {'schedule_time': campaign.schedule_time, 'timewarp': "false", "batch_delay":"false"}

    return f.post_to_mailchimp(brand, route, json.dumps(data))

def unschedule_campaign(campaign):
    brand = f.GetBrandByID(campaign.brand_id)
    route = 'campaigns/%s/actions/unschedule' % campaign.mailchimp_id
    data_str = None
    return f.post_to_mailchimp(brand, route, data_str)

def get_send_checklist(brand_id, mailchimp_id):
    brand = f.GetBrandByID(brand_id)
    route = 'campaigns/%s/send-checklist' % mailchimp_id
    data_str = None

    status, response = f.post_to_mailchimp(brand, route, data_str, method="GET")
    if not status:
        return False, False, response
    j_response = json.loads(response)
    if j_response['is_ready']:
        return True, True, []
    else:
        return True, False, j_response['items']

def replicate_campaign(campaign, user):
    brand = f.GetBrandByID(campaign.brand_id)
    route = 'campaigns/%s/actions/replicate' % campaign.mailchimp_id
    data_str = None
    status, response = f.post_to_mailchimp(brand, route, data_str)
    if not status:
        return False, response

    j_response = json.loads(response)
    return post_mailchimp_campaign_to_db(campaign.brand_id, campaign.folder_id, j_response, user, True, campaign.email_id)

def post_mailchimp_campaign_to_db(brand_id, folder_id, j_response, user, replicated=False, email_id=None):
    mailchimp_id = j_response['id']
    brand_id = brand_id
    folder_id = folder_id
    if not replicated:
        name = j_response['settings']['title']
    else:
        name = {'name': j_response['settings']['title'], 'id': email_id}
    type = j_response['type']
    campaign_status = j_response['status']
    emails_sent = j_response['emails_sent']
    send_time = None
    if j_response['send_time'] != "":
        send_time = j_response['send_time']
    created = j_response['create_time']
    content_type = j_response['content_type']
    list_mailchimp_id = j_response['recipients']['list_id']
    segment_text = j_response['recipients']['segment_text']
    recipient_count = j_response['recipients']['recipient_count']
    saved_segment_id = None
    if 'segment_opts' in j_response['recipients']:
        saved_segment_id = j_response['recipients']['segment_opts']['saved_segment_id']
    subject_line = j_response['settings']['subject_line']
    from_name = j_response['settings']['from_name']
    reply_to = j_response['settings']['reply_to']
    authenticate = j_response['settings']['authenticate']
    auto_footer = j_response['settings']['auto_footer']
    inline_css = j_response['settings']['inline_css']
    template_id = j_response['settings']['template_id']
    track_opens = j_response['tracking']['opens']
    track_clicks = j_response['tracking']['html_clicks']
    #print campaign['delivery_status']
    can_cancel = None
    delivery_status = None
    ds_emails_sent = None
    ds_emails_canceled = None
    delivery_status_enabled = j_response['delivery_status']['enabled']
    if j_response['delivery_status']['enabled']:
        can_cancel = j_response['delivery_status']['can_cancel']
        delivery_status = j_response['delivery_status']['status']
        ds_emails_sent = j_response['delivery_status']['emails_sent']
        ds_emails_canceled = j_response['delivery_status']['emails_canceled']

    return post_campaign_to_db(mailchimp_id, brand_id, folder_id, name, type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled, user)


def move_campaign(brand_id, campaign_id, folder_id, user):
    status, campaign = campaign_by_id(brand_id, campaign_id)
    if not status:
        return False, campaign
    campaign.folder_id = folder_id
    status, response = campaign_to_mailchimp(campaign, mailchimp_id=campaign.mailchimp_id, settings_only=True)
    if not status:
        return False, response
    #print response
    status, response = save_campaign('update', campaign, user)
    if not status:
        return False, response

    return True, campaign

def search(brand_id, search_type, search_for, search_contains, search_folder_id):
    fields = ['ID', 'MailChimp ID', 'Name', 'Folder']

    query = Campaign.query
    if search_for == 'name':
        if search_type == '2':
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.folder_id == search_folder_id, Campaign.name.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.name.like('%%%s%%' % search_contains)))
    elif search_for == 'subject_line':
        if search_type == '2':
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.folder_id == search_folder_id, Campaign.subject_line.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.subject_line.like('%%%s%%' % search_contains)))
    elif search_for == 'from_name':
        if search_type == '2':
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.folder_id == search_folder_id, Campaign.from_name.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.from_name.like('%%%s%%' % search_contains)))
    elif search_for == 'reply_to':
        if search_type == '2':
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.folder_id == search_folder_id, Campaign.reply_to.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(Campaign.brand_id == brand_id, Campaign.reply_to.like('%%%s%%' % search_contains)))
    campaigns = query.order_by(Campaign.name.asc()).all()
    rows = []
    for campaign in campaigns:
        status, folder = folders.get_folder_by_id(brand_id, folder_id=campaign.folder_id)
        if not status:
            return False, folder
        row = {}
        row['ID'] = campaign.id
        row['MailChimp ID'] = campaign.mailchimp_id
        if campaign.status == 'save':
            row['Name'] = "<a href='/campaigns/%s/detail'>%s</a>" % (campaign.id, campaign.name)
        else:
            row['Name'] = "<a href='/tracking/%s/detail'>%s</a>" % (campaign.id, campaign.name)
        row['Folder'] = folder.name
        rows.append(row)
    return True, {'Fields': fields, 'Data': rows}

def delete_campaign(brand_id, campaign_id):
    status, campaign = campaign_by_id(brand_id, campaign_id)
    if not status:
        return False, campaign
    brand = f.GetBrandByID(brand_id)
    status, response = f.delete_to_mailchimp(brand, "campaigns", campaign.mailchimp_id)
    if not status:
        return False, response
    try:
        db.session.delete(campaign)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def get_campaign_content(brand_id, campaign_id):
    status, campaign = campaign_by_id(brand_id, campaign_id)
    if not status:
        return False, campaign
    status, email = emails.email_by_id(brand_id, campaign.email_id)
    if not status:
        return False, "Email not found"

    return True, email

def all_variates(brand_id=None):
    query = VariateCampaign.query
    if brand_id != None:
        query = query.filter(VariateCampaign.brand_id == brand_id)
    return query.all()

def variate_by_id(brand_id, variate_id):
    variate = VariateCampaign.query.filter(and_(VariateCampaign.brand_id == brand_id, VariateCampaign.id == variate_id)).first()
    if not variate:
        return False, "VariateCampaign not found"
    return True, variate

def variate_by_mailchimp_id(brand_id, variate_id):
    variate = VariateCampaign.query.filter(and_(VariateCampaign.brand_id == brand_id, VariateCampaign.mailchimp_id == variate_id)).first()
    if not variate:
        return False, "VariateCampaign not found"
    return True, variate

def variate_exists_by_name(brand_id, name):
    return VariateCampaign.query.filter(and_(VariateCampaign.brand_id == brand_id, VariateCampaign.name == name)).count() > 0

def variate_to_form_request(campaign):
    request_object = {}
    request_object['ab_tests_segment_id'] = str(campaign.segment_id)
    request_object['ab_tests_list_id'] = str(campaign.list_id)
    request_object['ab_tests_name'] = campaign.name
    request_object['ab_tests_subject_line'] = campaign.subject_line
    request_object['ab_tests_from_name'] = campaign.from_name
    request_object['ab_tests_reply_to'] = campaign.reply_to
    request_object['ab_tests_test_type'] = campaign.test_type
    request_object['ab_tests_test_combinations'] = campaign.test_combinations
    request_object['ab_tests_test_size'] = campaign.test_size
    request_object['ab_tests_winning_criteria'] = campaign.winner_criteria
    request_object['ab_tests_wait_time'] = campaign.wait_time

    combinations = campaign.combinations.all()
    if len(combinations) > 0:
        combo1 = combinations[0]
        send_date_time_1 = combo1.send_time.split(' ')
        request_object['ab_tests_email_id_1'] = str(combo1.email_id)
        request_object['ab_tests_send_date_1'] = send_date_time_1[0]
        request_object['ab_tests_send_time_1'] = send_date_time_1[1]
        request_object['ab_tests_subject_line_1'] = combo1.subject_line
        request_object['ab_tests_from_name_1'] = combo1.from_name
        request_object['ab_tests_reply_to_1'] = combo1.reply_to

        combo2 = combinations[1]
        send_date_time_2 = combo2.send_time.split(' ')
        request_object['ab_tests_email_id_2'] = str(combo2.email_id)
        request_object['ab_tests_send_date_2'] = send_date_time_2[0]
        request_object['ab_tests_send_time_2'] = send_date_time_2[1]
        request_object['ab_tests_subject_line_2'] = combo2.subject_line
        request_object['ab_tests_from_name_2'] = combo2.from_name
        request_object['ab_tests_reply_to_2'] = combo2.reply_to

        if campaign.test_combinations == 3 and len(combinations) == 3:
            combo3 = combinations[1]
            send_date_time_3 = combo3.send_time.split(' ')
            request_object['ab_tests_email_id_3'] = str(combo3.email_id)
            request_object['ab_tests_send_date_3'] = send_date_time_3[0]
            request_object['ab_tests_send_time_3'] = send_date_time_3[1]
            request_object['ab_tests_subject_line_3'] = combo3.subject_line
            request_object['ab_tests_from_name_3'] = combo3.from_name
            request_object['ab_tests_reply_to_3'] = combo3.reply_to
        else:
            request_object['ab_tests_email_id_3'] = None
            request_object['ab_tests_send_date_3'] = None
            request_object['ab_tests_send_time_3'] = None
            request_object['ab_tests_subject_line_3'] = None
            request_object['ab_tests_from_name_3'] = None
            request_object['ab_tests_reply_to_3'] = None
    else:
        request_object['ab_tests_email_id_1'] = None
        request_object['ab_tests_send_date_1'] = None
        request_object['ab_tests_send_time_1'] = None
        request_object['ab_tests_subject_line_1'] = None
        request_object['ab_tests_from_name_1'] = None
        request_object['ab_tests_reply_to_1'] = None

        request_object['ab_tests_email_id_2'] = None
        request_object['ab_tests_send_date_2'] = None
        request_object['ab_tests_send_time_2'] = None
        request_object['ab_tests_subject_line_2'] = None
        request_object['ab_tests_from_name_2'] = None
        request_object['ab_tests_reply_to_2'] = None

        request_object['ab_tests_email_id_3'] = None
        request_object['ab_tests_send_date_3'] = None
        request_object['ab_tests_send_time_3'] = None
        request_object['ab_tests_subject_line_3'] = None
        request_object['ab_tests_from_name_3'] = None
        request_object['ab_tests_reply_to_3'] = None
    
    return request_object  

def request_to_variate(variate, request):
    try:
        segment_id = int(request['ab_tests_segment_id'])
        if segment_id != 0:
            variate.segment_id = segment_id
    except:
        pass
    variate.list_id = request['ab_tests_list_id']
    variate.name = request['ab_tests_name']
    variate.subject_line = request['ab_tests_subject_line']
    variate.from_name = request['ab_tests_from_name']
    variate.reply_to = request['ab_tests_reply_to']
    variate.test_type = request['ab_tests_test_type']
    variate.test_combinations = int(request['ab_tests_test_combinations'])
    variate.test_size = request['ab_tests_test_size']
    variate.winner_criteria = request['ab_tests_winning_criteria']
    variate.wait_time = request['ab_tests_wait_time']

    for combo in variate.combinations.all():
        db.session.delete(combo)
        db.session.commit()

    for idx in range(0, variate.test_combinations):
        comboidx = idx + 1
        combo = VariateCampaignCombination()
        if comboidx == 1 or variate.test_type == 'content':
            combo.email_id = request['ab_tests_email_id_%s' % comboidx]
        if variate.test_type == 'send_time':
            combo.send_time = '%s %s' % (request['ab_tests_send_date_%s' % comboidx], request['ab_tests_send_time_%s' % comboidx])
        if variate.test_type == 'subject_line':
            combo.subject_line = request['ab_tests_subject_line_%s' % comboidx]
        if variate.test_type == 'from_name':
            combo.from_name = request['ab_tests_from_name_%s' % comboidx]
            combo.reply_to = request['ab_tests_reply_to_%s' % comboidx]
        combo.recipients = 0
        variate.combinations.append(combo)
        print len(variate.combinations.all())
    return variate

def variate_to_mailchimp(variate, mailchimp_id=None, settings_only=True):
    status, mailchimp_obj = create_mailchimp_object_from_campaign(variate, campaign_type="variate")
    if not status:
        return False, mailchimp_obj
    brand = f.GetBrandByID(variate.brand_id)
    
    if mailchimp_id == None:
        status, resp = f.post_to_mailchimp(brand, "campaigns", json.dumps(mailchimp_obj))
    else:
        status, resp = f.patch_to_mailchimp(brand, "campaigns", json.dumps(mailchimp_obj), mailchimp_id)
    print status
    print resp
    if not status:
        return False, resp

    variate = update_variate_from_mailchimp_post(variate, resp)
    if not settings_only:
        status, response = variate_content_to_mailchimp(variate)
        if not status:
            return False, response
    return True, variate

def update_variate_from_mailchimp_post(variate, resp):
    j_response = json.loads(resp)
    variate.mailchimp_id = j_response['id']
    variate.status = j_response['status']

    return variate

def variate_content_to_mailchimp(variate):
    brand = f.GetBrandByID(variate.brand_id)
    data = {'variate_contents': []}
    for combo in variate.combinations:
        if combo.email_id != None:
            status, email = emails.email_by_id(variate.brand_id, combo.email_id)
            if not status:
                return False, email
            data['variate_contents'].append({'content_label': str(email.id), 'html': email.full_html})
    fh = open('/workspace/P01889/data_post', 'w')
    fh.write(json.dumps(data))
    fh.close()
    status, response = f.post_to_mailchimp(brand, "campaigns/%s/content" % variate.mailchimp_id, json.dumps(data), "PUT")
    if not status:
        return False, response
    return True, "OK"

def post_variate_to_db(brand, mailchimp_id, folder_id, name, campaign_status, send_time, created, list_mailchimp_id, saved_segment_id, winning_combination_id, winning_campaign_id, winner_criteria, wait_time, test_size, subject_lines, send_times, from_names, reply_to_addresses, contents, combinations, user):
    variate = VariateCampaign()
    variate.brand_id = brand.id
    variate.mailchimp_id = mailchimp_id
    variate.folder_id = folder_id
    variate.name = name
    variate.status = campaign_status
    if send_time != "":
        variate.send_time = send_time
    variate.created = created
    current_list = lists.list_by_mailchimp_id(brand.id, list_mailchimp_id)
    if not current_list:
        return False, "List not found"
    variate.list_id = current_list.id
    if saved_segment_id != None:
        status, current_segment = segment_by_mailchimp_id(brand.id, saved_segment_id)
        if not status:
            return False, current_segment
        variate.segment_id = current_segment.id
    variate.winning_combination_id = winning_combination_id
    variate.winning_campaign_id = winning_campaign_id
    variate.winner_criteria = winner_criteria
    variate.wait_time = wait_time
    variate.test_size = test_size

    if len(subject_lines) > 0:
        variate.test_type = 'subject_line'
        variate.test_combinations = len(subject_lines)
    elif len(send_times) > 0:
        variate.test_type == 'send_time'
        variate.test_combinations = len(send_times)
    elif len(from_names) > 0:
        variate.test_type == 'from_name'
        variate.test_combinations = len(from_names)
    elif len(contents) > 0:
        variate.test_type == 'content'
        variate.test_combinations = len(contents)

    for idx in range(0, variate.test_combinations):
        if idx == 0:
            variate.subject_line = subject_lines[idx]
            variate.from_name = from_names[idx]
            variate.reply_to = reply_to_addresses[idx]
        variate_combination = VariateCampaignCombination()
        if variate.test_type == 'subject_line':
            variate_combination.subject_line = subject_lines[idx]
        elif variate.test_type == 'send_time':
            variate_combination.send_time = send_times[idx]
        elif variate.test_type == 'from_name':
            variate_combination.from_name = from_names[idx]
            variate_combination.reply_to = reply_to_addresses[idx]
        elif variate.test_type == "content":
            variate_combination.email_id = int(contents[idx])
        if idx == 0 and variate.test_type != 'content':
            status, response = f.post_to_mailchimp(brand, "campaigns/%s/content" % variate.mailchimp_id, method="GET")
            if not status:
                return False, response
            j_response = json.loads(response)
            variate_contents = j_response['variate_contents']
            variate_combination.email_id = int(variate_contents[0]['content_label'])
        variate.combinations.append(variate_combination)

    try:
        variate.created_by = user.id
        db.session.add(variate)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)


def patch_variate_to_db(id, brand, mailchimp_id, name, campaign_status, send_time, created, list_mailchimp_id, saved_segment_id, winning_combination_id, winning_campaign_id, winner_criteria, wait_time, test_size, subject_lines, send_times, from_names, reply_to_addresses, contents, combinations, user):
    status, variate = variate_by_id(brand.id, id)
    if not status:
        return False, variate, user
    variate.brand_id = brand.id
    variate.mailchimp_id = mailchimp_id
    variate.name = name
    variate.status = campaign_status
    if send_time != None and send_time != "":
        variate.send_time = send_time
    variate.created = created
    current_list = lists.list_by_mailchimp_id(brand.id, list_mailchimp_id)
    if not current_list:
        return False, "List not found"
    variate.list_id = current_list.id
    if saved_segment_id != None:
        status, current_segment = segment_by_mailchimp_id(brand.id, saved_segment_id)
        if not status:
            return False, current_segment
        variate.segment_id = current_segment.id
    
    variate.winning_combination_id = winning_combination_id
    variate.winning_campaign_id = winning_campaign_id
    variate.winner_criteria = winner_criteria
    variate.wait_time = wait_time
    variate.test_size = test_size

    for combo in variate.combinations:
        db.session.delete(combo)
        db.session.commit()

    if len(subject_lines) > 1:
        #print 'sl'
        variate.test_type = 'subject_line'
        variate.test_combinations = len(subject_lines)
    elif len(send_times) > 1:
        #print 'st'
        variate.test_type = 'send_time'
        variate.test_combinations = len(send_times)
    elif len(from_names) > 1:
        #print 'fn'
        variate.test_type = 'from_name'
        variate.test_combinations = len(from_names)
    elif len(contents) > 1:
        #print 'ct'
        variate.test_type = 'content'
        variate.test_combinations = len(contents)

    for idx in range(0, variate.test_combinations):
        if idx == 0:
            variate.subject_line = subject_lines[idx]
            variate.from_name = from_names[idx]
            variate.reply_to = reply_to_addresses[idx]
            if send_times[idx] != None and send_times[idx] != "":
                variate.send_time = send_times[idx]
        variate_combination = VariateCampaignCombination()
        variate_combination.variate_campaign_id = variate.id
        variate_combination.mailchimp_id = combinations[idx]['id']
        if variate.test_type == 'subject_line':
            variate_combination.subject_line = subject_lines[idx]
        elif variate.test_type == 'send_time':
            variate_combination.send_time = send_times[idx]
        elif variate.test_type == 'from_name':
            variate_combination.from_name = from_names[idx]
            variate_combination.reply_to = reply_to_addresses[idx]
        elif variate.test_type == "content":
            variate_combination.email_id = int(contents[idx])
        if idx == 1 and variate.test_type != 'content':
            status, response = f.post_to_mailchimp(brand, "campaigns/%s/content" % variate.mailchimp_id, method="GET")
            if not status:
                return False, response
            j_response = json.loads(response)
            variate_contents = j_response['variate_contents']
            variate_combination.email_id = int(variate_contents[0]['content_label'])

        if len(combinations) > idx:
            variate_combination.recipients = int(combinations[idx]['recipients'])
        try:
            db.session.add(variate_combination)
            db.session.commit()
        except Exception as ex:
            return False, str(ex)
    try:
        variate.updated = datetime.datetime.now()
        variate.updated_by = user.id
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def move_variate(brand_id, variate_id, folder_id, user):
    status, variate = variate_by_id(brand_id, variate_id)
    if not status:
        return False, variate
    variate.folder_id = folder_id
    status, response = variate_to_mailchimp(variate, mailchimp_id=variate.mailchimp_id, settings_only=True)
    if not status:
        return False, response
    #print response
    status, response = save_campaign('update', variate, user)
    if not status:
        return False, response

    return True, variate

def search_variate_campaigns(brand_id, search_type, search_for, search_contains, search_folder_id):
    fields = ['ID', 'MailChimp ID', 'Name', 'Folder']

    query = VariateCampaign.query
    if search_for == 'name':
        if search_type == '2':
            query = query.filter(and_(VariateCampaign.brand_id == brand_id, VariateCampaign.folder_id == search_folder_id, VariateCampaign.name.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(VariateCampaign.brand_id == brand_id, VariateCampaign.name.like('%%%s%%' % search_contains)))
    variates = query.order_by(VariateCampaign.name.asc()).all()
    rows = []
    for variate in variates:
        status, folder = folders.get_folder_by_id(brand_id, folder_id=variate.folder_id)
        if not status:
            return False, folder
        row = {}
        row['ID'] = variate.id
        row['MailChimp ID'] = variate.mailchimp_id
        if variate.status == 'save':
            row['Name'] = "<a href='/ab_tests/%s/detail'>%s</a>" % (variate.id, variate.name)
        else:
            row['Name'] = "<a href='/tracking/%s/detail'>%s</a>" % (variate.id, variate.name)
        row['Folder'] = folder.name
        rows.append(row)
    return True, {'Fields': fields, 'Data': rows}

def delete_variate(brand_id, variate_id):
    status, variate = variate_by_id(brand_id, variate_id)
    if not status:
        return False, variate
    brand = f.GetBrandByID(brand_id)
    status, response = f.delete_to_mailchimp(brand, "campaigns", variate.mailchimp_id)
    if not status:
        return False, response
    try:
        db.session.delete(variate)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)