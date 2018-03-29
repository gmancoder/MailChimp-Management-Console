#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mailchimp import app, db
from sqlalchemy import *
import functions.core as f
import functions.lists as lists
import functions.brands as brands
import functions.users as users
import functions.segments as segments
import functions.folders as folders
import functions.templates as templates
import functions.emails as emails
import functions.campaigns as campaigns
import functions.tracking as tracking
import csv
import os
import sys
import json
import unidecode
import commands
SYNC_USER_ID = 2
MC_RECORDS_PER_PAGE = 10
PROJECT_ROOT = '/var/www/html/gmancoder.com/subdomains/mmc/'

def sync_list_merge_fields(brand, list_id, mmc_list, errors, user):
    total_merge_field_records = 10
    idx2 = 0
    while True:
        if idx2 > total_merge_field_records:
            break
        status, merge_field_response = f.post_to_mailchimp(brand, "lists/%s/merge-fields?offset=%d" % (list_id, idx2), method="GET")
        if not status:
            error = {'Method': 'ListMergeFields-Get', 'Error': merge_field_response}
            errors.append(error)
            break
        else:
            mc_merge_fields = json.loads(merge_field_response)
            if idx2 == 0:
                total_merge_field_records = mc_merge_fields['total_items']
            idx2 += MC_RECORDS_PER_PAGE
            for merge_field in mc_merge_fields['merge_fields']:
                merge_id = merge_field['merge_id']
                tag = merge_field['tag']
                name = merge_field['name']
                field_type = merge_field['type']
                required = merge_field['required']
                public = merge_field['public']
                display_order = merge_field['display_order']
                default_value = merge_field['default_value']
                options = merge_field['options']
                status, mmc_merge_field = lists.get_merge_field_by_tag(mmc_list.id, tag)
                if not status and mmc_merge_field == "Merge Field not found":
                    status, response = lists.add_merge_field_to_db(mmc_list.id, merge_id, tag, name, field_type, required, public, display_order, default_value, options, user, sync=True)
                    if not status:
                        error = {'Method': 'ListMergeFields-Add', 'Error': response}
                        errors.append(error)
                elif status:
                    status, response = lists.update_merge_field_to_db(mmc_merge_field.id, mmc_list.id, merge_id, tag, name, field_type, required, public, display_order, default_value, options, user, sync=True)
                    if not status:
                        error = {'Method': 'ListMergeFields-Update', 'Error': response}
                        errors.append(error)
                else:
                    error = {'Method': 'ListMergeFields-MMCGet', 'Error': merge_field_response}
                    errors.append(error)
    return errors

def sync_list_activity(brand, list_id, mmc_list, errors, user):
    total_activity = 10
    idx2 = 0
    while True:
        if idx2 > total_activity:
            break
        status, activity_response = f.post_to_mailchimp(brand, "lists/%s/activity?offset=%d" % (list_id, idx2), method="GET")
        if not status:
            error = {'Method': 'ListActivity-Get', 'Error': activity_response}
            errors.append(error)
            break
        else:
            mc_list_activity = json.loads(activity_response)
            if idx2 == 0:
                total_activity = mc_list_activity['total_items']
            idx2 += MC_RECORDS_PER_PAGE
            if 'activity' not in mc_list_activity:
                break
            for request_object in mc_list_activity['activity']:
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
                status, response = lists.post_activity(brand.id, mmc_list.id, day, emails_sent, unique_opens, recipient_clicks, hard_bounce, soft_bounce, subs, unsubs, other_adds, other_removes, user)
                if not status:
                    error = {'Method': 'ListActivity-Post', 'Error': response}
                    errors.append(error)
    return errors

def sync_list_subscribers(brand, list_id, mmc_list, errors, user):
    total_subscribers = 10
    idx2 = 0
    while True:
        if idx2 > total_subscribers:
            break
        status, subscriber_response = f.post_to_mailchimp(brand, "lists/%s/members?offset=%d" % (list_id, idx2), method="GET")
        if not status:
            error = {'Method': 'ListMembers-Get', 'Error': subscriber_response}
            errors.append(error)
            break
        else:
            mc_subscribers = json.loads(subscriber_response)
            if idx2 == 0:
                total_subscribers = mc_subscribers['total_items']
            idx2 += MC_RECORDS_PER_PAGE
            for subscriber in mc_subscribers['members']:
                email_id = subscriber['id']
                email_address = subscriber['email_address'],
                unique_email_id = subscriber['unique_email_id'],
                email_type = subscriber['email_type'],
                email_status = subscriber['status'],
                merge_fields = subscriber['merge_fields']
                timestamp_signup = None
                last_changed = None
                if subscriber['timestamp_signup'].strip() !="":
                    timestamp_signup = subscriber['timestamp_signup']
                elif subscriber['timestamp_opt'].strip() != "":
                    timestamp_signup = subscriber['timestamp_opt']
                if subscriber['last_changed'] != "":
                    last_changed = subscriber['last_changed']
                location = subscriber['location']
                
                status, mc_subscriber = lists.get_subscriber_by_email_id(brand.id, email_id, list_id)
                if not status:
                    status, new_subscriber = lists.add_subscriber_to_db(brand.id, mmc_list.id, email_id, email_address, unique_email_id, email_type, email_status, timestamp_signup, last_changed, location, merge_fields, user, sync=True)
                    if not status:
                        error = {'Method': 'ListMembers-Add', 'Error': new_subscriber}
                        errors.append(error)
                    else:
                        status, mc_subscriber = lists.get_subscriber_by_email_id(brand.id, email_id, list_id)
                else:
                    status, new_subscriber = lists.update_subscriber_to_db(mc_subscriber.id, email_type, email_status, last_changed, location, merge_fields, user, sync=True)
                    if not status:
                        error = {'Method': 'ListMembers-Update', 'Error': new_subscriber}
                        errors.append(error)
    return errors
def sync_segments(brand, list_id, mmc_list, errors, user):
    total_segments = 10
    idx2 = 0
    while True:
        if idx2 > total_segments:
            break
        status, segments_response = f.post_to_mailchimp(brand, "lists/%s/segments?offset=%d" % (list_id, idx2), method="GET")
        if not status:
            error = {'Method': 'ListSegments-Get', 'Error': segments_response}
            errors.append(error)
            break
        else:
            mc_list_segments = json.loads(segments_response)
            if idx2 == 0:
                total_segments = mc_list_segments['total_items']
            idx2 += MC_RECORDS_PER_PAGE
            if 'segments' not in mc_list_segments:
                break
            for segment in mc_list_segments['segments']:
                mailchimp_id = segment['id']
                name = segment['name']
                list_mailchimp_id = segment['list_id']
                match = None
                conditions = []
                if 'options' in segment:
                    match = segment['options']['match']
                    conditions = segment['options']['conditions']
                segment_type = segment['type']
                segment_folder = folders.get_root_folder(brand.id, "segments")
                folder_id = segment_folder.id
                status, current_segment = segments.segment_by_mailchimp_id(brand.id, str(mailchimp_id))
                if not status:
                    method = "Add"
                    status, response = segments.segment_to_db(brand.id, folder_id, str(mailchimp_id), name, segment_type, match, user, conditions, list_id=mmc_list.id)
                else:
                    method = "Update"
                    status, response = segments.segment_to_db(brand.id, folder_id, str(mailchimp_id), name, segment_type, match, user, conditions, list_id=mmc_list.id, id=current_segment.id)
                if not status:
                    error = {'Method': 'ListSegments-%s' % method, 'Error': segments_response}
                    errors.append(error)
                else:
                    if method == 'Add':
                        status, current_segment = segments.segment_by_mailchimp_id(brand.id, str(mailchimp_id))
                    method = 'ApplySubscribers'
                    status, response = segments.apply_segment_subscribers_from_mailchimp(brand.id, current_segment.id)
                    if not status:
                        error = {'Method': 'ListSegments-%s' % method, 'Error': segments_response}
                        errors.append(error)
    return errors




def sync_lists(brand, errors, user):
    list_offset = 0
    idx = 0
    total_list_records = 10
    while True:
        if idx > total_list_records:
            break
        status, list_response = f.post_to_mailchimp(brand, "lists?offset=%d" % idx, method="GET")
        if not status:
            error = {'Method': 'Lists-Get', 'Error': list_response}
            errors.append(error)
            break
        else:
            mc_lists = json.loads(list_response)
            #print mc_lists
            if idx == 0:
                total_list_records = mc_lists['total_items']
            idx += MC_RECORDS_PER_PAGE
            for lst in mc_lists['lists']:
                list_id = lst['id']
                name = lst['name']
                request = {'id': list_id, 'name': name, "contact_company": lst['contact']['company'],
                           "contact_address1": lst['contact']['address1'],
                           "contact_address2": lst['contact']['address2'],
                           "contact_city": lst['contact']['city'],
                           "contact_state": lst['contact']['state'],
                           "contact_zip": lst['contact']['zip'],
                           "contact_country": lst['contact']['country'],
                           "contact_phone": lst['contact']['phone'],
                           "campaign_default_from_name": lst['campaign_defaults']['from_name'],
                           "campaign_default_from_email": lst['campaign_defaults']['from_email'],
                           "campaign_default_subject": lst['campaign_defaults']['subject'],
                           "campaign_default_language": lst['campaign_defaults']['language'],
                           "permission_reminder": lst['permission_reminder'],
                           "notify_on_subscribe": lst['notify_on_subscribe'],
                           "notify_on_unsubscribe": lst['notify_on_unsubscribe'],
                           "email_type_option": int(lst['email_type_option']),
                           "visibility": lst['visibility'],
                           'campaign_last_sent': lst['stats']['campaign_last_sent']}
                mmc_list = lists.list_by_mailchimp_id(brand.id, list_id)
                if not mmc_list:
                    status, response = lists.add_list_to_database(brand.id, request, user)
                    if not status:
                        error = {'Method': 'Lists-Add', 'Error': response}
                        errors.append(error)
                    else:
                        mmc_list = lists.list_by_mailchimp_id(brand.id, list_id)
                else:
                    status, response = lists.update_list_to_database(request, user, mmc_list.id)
                    if not status:
                        error = {'Method': 'Lists-Update', 'Error': response}
                        errors.append(error)
                
                # List Merge Fields
                errors = sync_list_merge_fields(brand, list_id, mmc_list, errors, user)
                
                # List Activity
                errors = sync_list_activity(brand, list_id, mmc_list, errors, user)

                # List Subscribers
                errors = sync_list_subscribers(brand, list_id, mmc_list, errors, user)

                # Segments
                errors = sync_segments(brand, list_id, mmc_list, errors, user)
                            
    return errors

def sync_templates(brand, errors, user):
    idx = 0
    total_template_records = 10
    while True:
        if idx > total_template_records:
            break
        status, template_response = f.post_to_mailchimp(brand, "templates?offset=%d&type=user" % idx, method="GET")
        if not status:
            error = {'Method': 'Templates-Get', 'Error': template_response}
            errors.append(error)
            break
        else:
            mc_templates = json.loads(template_response)
            #print mc_templates
            if idx == 0:
                total_template_records = mc_templates['total_items']
            idx += MC_RECORDS_PER_PAGE
            for template in mc_templates['templates']:
                category = template['category']
                category_id = None
                if category != None and category.strip() != "":
                    status, current_categories = get_template_category_by_name(brand.id, category, True)
                    if len(current_categories) > 0:
                        category_id = current_categories[0].id
                    else:
                        category_folder = folders.get_root_folder(brand.id, "template_categories")
                        status, new_category = add_template_category(brand.id, category, category_folder.id, user.id, True)
                        if not status:
                            error = {'Method': 'TemplateCategories-Add', 'Error': new_category}
                            errors.append(error)
                            continue
                        else:
                            category_id = new_category.id
                template_folder = folders.get_root_folder(brand.id, "templates")
                folder_id = template_folder.id
                mailchimp_id = template['id']
                name = template['name']
                template_type = template['type']
                active = template['active']
                thumbnail = template['thumbnail']
                status, template_content_response = f.post_to_mailchimp(brand, "templates/%s/default-content" % mailchimp_id, method="GET")
                if not status:
                    error = {'Method': 'TemplateContent-Get', 'Error': template_content_response}
                    errors.append(error)
                    continue
                
                template_content = json.loads(template_content_response)
                sections = template_content['sections']
                status, current_template = templates.template_by_mailchimp_id(brand.id, str(mailchimp_id))
                if not status:
                    method = "Add"
                    status, response = templates.template_to_db(brand.id, category_id, folder_id, str(mailchimp_id), name, template_type, active, thumbnail, user, sections=sections)
                else:
                    method = "Update"
                    status, response = templates.template_to_db(brand.id, category_id, folder_id, str(mailchimp_id), name, template_type, active, thumbnail, user, sections=sections, id=current_template.id)
                if not status:
                    error = {'Method': 'Templates-%s' % method, 'Error': response}
                    errors.append(error)
    return errors

def sync_emails(brand, errors, user):
    idx = 0
    total_email_records = 10
    while True:
        if idx > total_email_records:
            break
        status, email_response = f.post_to_mailchimp(brand, "campaigns?offset=%d&type=regular" % idx, method="GET")
        if not status:
            error = {'Method': 'Emails-Get', 'Error': email_response}
            errors.append(error)
            break
        else:
            mc_emails = json.loads(email_response)
            #print mc_emails
            if idx == 0:
                total_email_records = mc_emails['total_items']
            idx += MC_RECORDS_PER_PAGE
            for campaign in mc_emails['campaigns']:
                mailchimp_id = campaign['id']
                last_sent = campaign['send_time']
                if last_sent == '':
                    last_sent = None
                name = campaign['settings']['title']
                subject_line = campaign['settings']['subject_line']
                template_mailchimp_id = campaign['settings']['template_id']
                template_id = None
                status, email_template = templates.template_by_mailchimp_id(brand.id, str(template_mailchimp_id))
                if status:
                    template_id = email_template.id
                email_folder = folders.get_root_folder(brand.id, "emails")
                folder_id = email_folder.id

                status, campaign_content_response = f.post_to_mailchimp(brand, "campaigns/%s/content" % mailchimp_id, method="GET")
                if not status:
                    error = {'Method': 'EmailContent-Get', 'Error': campaign_content_response}
                    errors.append(error)
                    continue
                
                campaign_content = json.loads(campaign_content_response)
                html = unidecode.unidecode(campaign_content['html'])
                
                status, current_email = emails.email_by_campaign_name(brand.id, name)
                if not status:
                    method = "Add"
                    status, response = emails.email_to_db(brand.id, template_id, name, subject_line, folder_id, user, last_sent, html)
                else:
                    method = "Update"
                    status, response = emails.email_to_db(brand.id, template_id, name, subject_line, folder_id, user, last_sent, html, id=current_email.id)

                if not status:
                    error = {'Method': 'Emails-%s' % method, 'Error': response}
                    errors.append(error)
                
                # Email to Image
                email_id = response  
                email_path = '%semails/%s/%s.html' % (PROJECT_ROOT, brand.id, email_id)
                image_path = '%sstatic/img/emails/%s/%s.jpg' % (PROJECT_ROOT, brand.id, email_id)
                fh = open(email_path, 'w')
                fh.write(html)
                fh.close()
                cmd = 'xvfb-run wkhtmltoimage -q "%s" "%s"' % (email_path, image_path)
                status, response = commands.getstatusoutput(cmd)
                if status != 0:
                    error = {'Method': 'Emails-Screenshot', 'Error': response}
                    errors.append(error)
    return errors

def sync_campaigns(brand, errors, user):
    idx = 0
    total_campaign_records = 10
    while True:
        if idx > total_campaign_records:
            break
        status, campaign_response = f.post_to_mailchimp(brand, "campaigns?offset=%d&type=regular" % idx, method="GET")
        if not status:
            error = {'Method': 'Campaigns-Get', 'Error': campaign_response}
            errors.append(error)
            break
        else:
            mc_campaigns = json.loads(campaign_response)
            #print mc_campaigns
            if idx == 0:
                total_campaign_records = mc_campaigns['total_items']
            idx += MC_RECORDS_PER_PAGE
            for campaign in mc_campaigns['campaigns']:
                mailchimp_id = campaign['id']
                print mailchimp_id
                campaign_type = campaign['type']
                #print campaign_type
                campaign_folder = folders.get_root_folder(brand.id, "campaigns")
                folder_id = campaign_folder.id
                name = campaign['settings']['title']
                #print name
                campaign_status = campaign['status']
                emails_sent = campaign['emails_sent']
                #print emails_sent
                send_time = campaign['send_time']
                created = campaign['create_time']
                content_type = campaign['content_type']
                list_mailchimp_id = campaign['recipients']['list_id']
                segment_text = campaign['recipients']['segment_text']
                recipient_count = campaign['recipients']['recipient_count']
                saved_segment_id = None
                if 'segment_opts' in campaign['recipients']:
                    saved_segment_id = campaign['recipients']['segment_opts']['saved_segment_id']
                subject_line = campaign['settings']['subject_line']
                from_name = campaign['settings']['from_name']
                reply_to = campaign['settings']['reply_to']
                authenticate = campaign['settings']['authenticate']
                auto_footer = campaign['settings']['auto_footer']
                inline_css = campaign['settings']['inline_css']
                template_id = campaign['settings']['template_id']
                track_opens = campaign['tracking']['opens']
                track_clicks = campaign['tracking']['html_clicks']
                #print campaign['delivery_status']
                can_cancel = None
                delivery_status = None
                ds_emails_sent = None
                ds_emails_canceled = None
                delivery_status_enabled = campaign['delivery_status']['enabled']
                if campaign['delivery_status']['enabled']:
                    can_cancel = campaign['delivery_status']['can_cancel']
                    delivery_status = campaign['delivery_status']['status']
                    ds_emails_sent = campaign['delivery_status']['emails_sent']
                    ds_emails_canceled = campaign['delivery_status']['emails_canceled']
                status, current_campaign = campaigns.campaign_by_mailchimp_id(brand.id, str(mailchimp_id))
                if not status:
                    method = "Add"
                    #print 'Adding'
                    status, response = campaigns.post_campaign_to_db(str(mailchimp_id), brand.id, folder_id, name, campaign_type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled, user, True)
                else:
                    method = "Update"
                    #print 'Updating'
                    status, response = campaigns.patch_campaign_to_db(current_campaign.id, str(mailchimp_id), brand.id, None, name, campaign_type, campaign_status, emails_sent, send_time, created, content_type, list_mailchimp_id, segment_text, recipient_count, saved_segment_id, subject_line, from_name, reply_to, authenticate, auto_footer, inline_css, template_id, track_opens, track_clicks, delivery_status_enabled, can_cancel, delivery_status, ds_emails_sent, ds_emails_canceled, user, True)
                #print '%s: %s' % (status, response)
                if not status:
                    error = {'Method': 'Campaigns-%s' % method, 'Error': response}
                    errors.append(error)

                if 'report_summary' in campaign:
                    ##print campaign['report_summary']
                    status, current_campaign = campaigns.campaign_by_mailchimp_id(brand.id, str(mailchimp_id))
                    #print '%s: %s' % (status, current_campaign)
                    if not status:
                        error = {'Method': 'Campaigns-GetForTracking', 'Error': current_campaign}
                        errors.append(error)
                    else:
                        errors = tracking.track_campaign(current_campaign, errors, campaign['report_summary'])
    return errors

def sync_variates(brand, errors, user):
    idx = 0
    total_variate_records = 10
    while True:
        if idx > total_variate_records:
            break
        status, variate_response = f.post_to_mailchimp(brand, "campaigns?offset=%d&type=variate" % idx, method="GET")
        if not status:
            error = {'Method': 'Campaigns-Get', 'Error': variate_response}
            errors.append(error)
            break
        else:
            mc_campaigns = json.loads(variate_response)
            #print mc_campaigns
            if idx == 0:
                total_variate_records = mc_campaigns['total_items']
            idx += MC_RECORDS_PER_PAGE
            for campaign in mc_campaigns['campaigns']:
                #print campaign
                mailchimp_id = campaign['id']
                name = campaign['settings']['title']
                campaign_status = campaign['status']
                send_time = campaign['send_time']
                if send_time == "":
                    send_time = None
                created = campaign['create_time']
                list_mailchimp_id = campaign['recipients']['list_id']
                saved_segment_id = None
                if 'segment_opts' in campaign['recipients']:
                    saved_segment_id = campaign['recipients']['segment_opts']['saved_segment_id']
                winning_combination_id = campaign['variate_settings']['winning_combination_id']
                winning_campaign_id = campaign['variate_settings']['winning_campaign_id']
                winner_criteria = campaign['variate_settings']['winner_criteria']
                wait_time = campaign['variate_settings']['wait_time']
                test_size = campaign['variate_settings']['test_size']
                subject_lines = campaign['variate_settings']['subject_lines']
                send_times = campaign['variate_settings']['send_times']
                from_names = campaign['variate_settings']['from_names']
                reply_to_addresses = campaign['variate_settings']['reply_to_addresses']
                contents = campaign['variate_settings']['contents']
                combinations = campaign['variate_settings']['combinations']
                #print combinations
                status, current_campaign = campaigns.variate_by_mailchimp_id(brand.id, str(mailchimp_id))
                if not status:
                    method = "Add"
                    variate_folder = folders.get_root_folder(brand.id, "ab_tests")
                    folder_id = variate_folder.id
                    status, response = campaigns.post_variate_to_db(brand, str(mailchimp_id), folder_id, name, campaign_status, send_time, created, list_mailchimp_id, saved_segment_id, winning_combination_id, winning_campaign_id, winner_criteria, wait_time, test_size, subject_lines, send_times, from_names, reply_to_addresses, contents, combinations, user)
                else:
                    method = "Update"
                    status, response = campaigns.patch_variate_to_db(current_campaign.id, brand, str(mailchimp_id), name, campaign_status, send_time, created, list_mailchimp_id, saved_segment_id, winning_combination_id, winning_campaign_id, winner_criteria, wait_time, test_size, subject_lines, send_times, from_names, reply_to_addresses, contents, combinations, user)
                    #print response
                if not status:
                    error = {'Method': 'Campaigns-%s' % method, 'Error': response}
                    errors.append(error)

                if 'report_summary' in campaign:
                    #print campaign['report_summary']
                    status, current_campaign = campaigns.variate_by_mailchimp_id(brand.id, str(mailchimp_id))
                    if not status:
                        error = {'Method': 'Campaigns-GetForTracking', 'Error': current_campaign}
                        errors.append(error)
                    else:
                        errors = tracking.track_variate(current_campaign, errors, campaign['report_summary'])

    return errors

with app.app_context():
    errors = []
    user = users.user_by_id(SYNC_USER_ID)
    all_brands = brands.all_brands()
    for brand in all_brands:
        # Lists
        errors = sync_lists(brand, errors, user)
        # Templates
        errors = sync_templates(brand, errors, user)
        # Emails
        errors = sync_emails(brand, errors, user)
        # Campaigns
        errors = sync_campaigns(brand, errors, user)
        # Variates
        errors = sync_variates(brand, errors, user)
    print errors
