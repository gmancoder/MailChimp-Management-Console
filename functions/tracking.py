#!/usr/bin/env python
from models.shared import db
from models.list_subscribers import *
from models.tracking import *
from models.campaigns import *
from sqlalchemy import *
import core as f
import forms
import glob
import os
import csv
import folders
import inflection
import datetime
import campaigns
import lists
import emails
import segments

def campaign_tracking_fields():
    return ['campaign_id',
            'campaign_name',
            'email_name',
            'list_name',
            'segment_name',
            'send_time',
            'subject_line',
            'from_name',
            'reply_to',
            'number_sent',
            'number_delivered',
            'delivery_rate',
            'number_hard_bounces',
            'percent_hard_bounces',
            'number_soft_bounces',
            'percent_soft_bounces',
            'number_opens',
            'percent_opens',
            'number_unique_opens',
            'number_clicks',
            'percent_clicks',
            'number_unique_clicks',
            'number_unsubs',
            'total_orders',
            'total_spent',
            'total_revenue']

def ab_test_tracking_fields():
    return list(campaign_tracking_fields() + ['variate_campaign_winner_criteria',
                                                'variate_campaign_wait_time',
                                                'variate_campaign_test_size',
                                                'variate_campaign_test_type',
                                                'variate_campaign_test_combinations',
                                                'variate_campaign_details'])

def get_all(brand_id=None, tracking_type=None):
    query = TrackedCampaign.query
    if(brand_id != None and tracking_type != None):
        query = query.filter(and_(TrackedCampaign.brand_id == brand_id, TrackedCampaign.type == tracking_type))
    elif(brand_id != None):
        query = query.filter(TrackedCampaign.brand_id == brand_id)
    elif(tracking_type != None):
        query = query.filter(TrackedCampaign.type == tracking_type)
    return query.all()

def tracking_by_id(brand_id, tracking_id):
    tracked = TrackedCampaign.query.filter(and_(TrackedCampaign.brand_id == brand_id, TrackedCampaign.id == tracking_id)).first()
    if not tracked:
        return False, "Tracking not found"
    return True, tracked

def tracking_by_campaign_id(brand_id, campaign_id, campaign_type):
    tracked = TrackedCampaign.query.filter(and_(TrackedCampaign.brand_id == brand_id, TrackedCampaign.campaign_id == campaign_id, TrackedCampaign.type == campaign_type)).first()
    if not tracked:
        return False, "Tracking not found"
    return True, tracked

def tracking_by_folder(folder_id):
    return TrackedCampaign.query.filter(TrackedCampaign.folder_id == folder_id).all()

def tracking_to_export_request(tracking):
    request = {}
    request['campaign_id'] = tracking.campaign_id
    request['campaign_name'] = tracking.campaign_name
    request['email_name'] = tracking.email_name
    request['list_name'] = tracking.list_name
    request['segment_name'] = tracking.segment_name
    request['send_time'] = tracking.send_time
    request['subject_line'] = tracking.subject_line
    request['from_name'] = tracking.from_name
    request['reply_to'] = tracking.reply_to
    request['number_sent'] = tracking.number_sent
    request['number_delivered'] = tracking.number_delivered
    request['delivery_rate'] = tracking.delivery_rate
    request['number_hard_bounces'] = tracking.number_hard_bounces
    request['percent_hard_bounces'] = tracking.percent_hard_bounces
    request['number_soft_bounces'] = tracking.number_soft_bounces
    request['percent_soft_bounces'] = tracking.percent_soft_bounces
    request['number_opens'] = tracking.number_opens
    request['percent_opens'] = tracking.percent_opens
    request['number_unique_opens'] = tracking.number_unique_opens
    request['number_clicks'] = tracking.number_clicks
    request['percent_clicks'] = tracking.percent_clicks
    request['number_unique_clicks'] = tracking.number_unique_clicks
    request['number_unsubs'] = tracking.number_unsubs
    request['total_orders'] = tracking.total_orders
    request['total_spent'] = tracking.total_spent
    request['total_revenue'] = tracking.total_revenue
    return request

def track_campaign(campaign, errors, report_summary={}):
    tracked, errors, method = _process_campaign_tracking(campaign, "campaigns", errors, report_summary)
    if tracked != None:
        # Email
        status, tracked_email = emails.email_by_id(campaign.brand_id, campaign.email_id)
        if not status:
            errors.append({'Method': 'CampaignTracking - Get Email', 'Error': '%s' % tracked_email})
        tracked.email_name = tracked_email.name
        tracked.email_id = tracked_email.id
        if campaign.is_rtm:
            tracked.type = "rtm"
        status, response = _save_tracking(tracked, method)
        if not status:
            errors.append({'Method': 'CampaignTracking - Save', 'Error': '%s' % response})
    return errors

def track_variate(variate, errors, report_summary={}):
    tracked, errors, method = _process_campaign_tracking(variate, "ab_tests", errors, report_summary)
    if tracked != None:
        tracked.variate_campaign_winner_criteria = variate.winner_criteria
        tracked.variate_campaign_wait_time = variate.wait_time
        tracked.variate_campaign_test_size = variate.test_size
        tracked.variate_campaign_test_type = variate.test_type
        tracked.variate_campaign_test_combinations = variate.test_combinations
        idx = 0
        if tracked.variate_campaign_details.count() > 0:
            tracked.variate_campaign_details.delete()
            #db.session.commit()
        for combo in variate.combinations.all():
            idx += 1

            tracked_detail = TrackedCampaignVariateDetail()
            
            # Email
            if combo.email_id != None and combo.email_id != "":
                status, tracked_email = emails.email_by_id(variate.brand_id, combo.email_id)
                if not status:
                    errors.append({'Method': 'VariateTracking - Get Email', 'Error': '%s' % tracked_email})
                else:
                    if variate.test_type != "content":
                        tracked.email_name = tracked_email.name
                        tracked.email_id = tracked_email.id
                    else:
                        tracked_detail.email_name = tracked_email.name
                        tracked_detail.email_id = tracked_email.id
            
            if combo.mailchimp_id == variate.winning_combination_id:
                tracked_detail.is_winner = True

            tracked_detail.send_time = combo.send_time
            tracked_detail.subject_line = combo.subject_line
            tracked_detail.from_name = combo.from_name
            tracked_detail.reply_to = combo.reply_to
            tracked_detail.recipients = combo.recipients

            if method == 'new':
                tracked.variate_campaign_details.append(tracked_detail)
            else:
                tracked_detail.tracking_id = tracked.id
                db.session.add(tracked_detail)
                db.session.commit()
        status, response = _save_tracking(tracked, method)
        if not status:
            errors.append({'Method': 'VariateTracking - Save', 'Error': '%s' % response})
    return errors

def sync_tracking():
    errors = []
    all_campaigns = campaigns.all_campaigns()
    for campaign in all_campaigns:
        errors = track_campaign(campaign, errors)
    variates = campaigns.all_variates()
    if variates != None and len(variates) > 0:
        for variate in variates:
            errors = track_variate(variate, errors)
    return errors

def _process_campaign_tracking(campaign, campaign_type, errors, report_summary={}):
    opens = []
    clicks = []
    method = "update"
    if campaign.status in ('sent', 'sending'):
        status, tracked = tracking_by_campaign_id(campaign.brand_id, campaign.id, campaign_type)
        if not status:
            tracked = TrackedCampaign()
            method = "new"
            folder_type = '%s_tracking' % inflection.singularize(campaign_type)
            print folder_type
            tracked_folder = folders.get_root_folder(campaign.brand_id, folder_type)
            tracked.folder_id = tracked_folder.id
        tracked.brand_id = campaign.brand_id
        tracked.campaign_name = campaign.name
        tracked.campaign_id = campaign.id
        tracked.type = campaign_type
        # List
        tracked_list = lists.list_by_id(campaign.brand_id, campaign.list_id)
        if not tracked_list:
            errors.append({'Method': '%s - List', 'Error': '%s' % (campaign.name, "List not found")})
        tracked.list_name = tracked_list.name
        
        # Segment
        if campaign.segment_id != None:
            status, tracked_segment = segments.segment_by_id(campaign.brand_id, campaign.segment_id)
            if not status:
                errors.append({'Method': '%s - Segment', 'Error': '%s' % (campaign.name, "Segment not found")})
            tracked.segment_name = tracked_segment.name

        tracked.send_time = campaign.send_time
        tracked.subject_line = campaign.subject_line
        tracked.from_name = campaign.from_name
        tracked.reply_to = campaign.reply_to
        tracked.number_sent = 0
        tracked.number_delivered = 0
        tracked.delivery_rate = 0
        tracked.number_hard_bounces = 0
        tracked.percent_hard_bounces = 0
        tracked.number_soft_bounces = 0
        tracked.percent_soft_bounces = 0
        tracked.number_unsubs = 0
        campaign_activity = campaign.activity.all()
        for activity in campaign_activity:
            if activity.action == 'sent':
                tracked.number_sent += 1
            elif activity.action == 'bounce':
                   if activity.type == 'hard':
                       tracked.number_hard_bounces += 1
                   elif activity.type == 'soft':
                       tracked.number_soft_bounces += 1
            elif activity.action == 'unsub':
                tracked.number_unsubs += 1
        tracked.number_delivered = tracked.number_sent - (tracked.number_hard_bounces + tracked.number_soft_bounces)
        if tracked.number_sent > 0:
            tracked.delivery_rate = float(tracked.number_delivered) / float(tracked.number_sent)
        if tracked.number_delivered > 0:
            tracked.percent_hard_bounces = float(tracked.number_hard_bounces) / float(tracked.number_delivered)
            tracked.percent_soft_bounces = float(tracked.number_soft_bounces) / float(tracked.number_delivered)
        
        for key, value in report_summary.items():
            if key == 'opens':
                tracked.number_opens = value
            elif key == 'unique_opens':
                tracked.number_unique_opens = value
            elif key == 'open_rate':
                tracked.percent_opens = value
            elif key == 'clicks':
                tracked.number_clicks = value
            elif key == 'subscriber_clicks':
                tracked.number_unique_clicks = value
            elif key == 'click_rate':
                tracked.percent_clicks = value
            elif key == 'ecommerce':
                for k,v in value.items():
                    if k == 'total_orders':
                        tracked.total_orders = v
                    elif k == 'total_spent':
                        tracked.total_spent = v
                    elif k == 'total_revenue':
                        tracked.total_revenue = v

        
        return tracked, errors, method
    return None, errors, method

def _save_tracking(tracked, method, user=None):
    try:
        if method == 'new':
            if user == None:
                tracked.created_by = 2
            else:
                tracked.created_by = user.id
            db.session.add(tracked)
        else:
            tracked.updated = datetime.datetime.now()
            if user == None:
                tracked.updated_by = 2
            else:
                tracked.updated_by = user.id
        db.session.commit()
        return True, tracked
    except Exception as ex:
        return False, str(ex)

def move(brand_id, tracking_id, folder_id, user):
    status, tracked = tracking_by_id(brand_id, tracking_id)
    if not status:
        return False, tracked
    tracked.folder_id = folder_id
    status, tracked = _save_tracking(tracked, "update", user)
    if not status:
        return False, tracked
    return True, "OK"

def export_tracking_summary(export_def, writer, log_writer):
    fields = []
    objects = []
    results = {'total': 0, 'errors': 0}
    for field in export_def.fields.all():
        fields.append(field.field_name)

    for obj in export_def.target_objects.all():
        objects.append(obj.object_id)

    writer.writerow(fields)
    tracking = TrackedCampaign.query.filter(and_(TrackedCampaign.brand_id == export_def.brand_id, TrackedCampaign.id.in_(objects))).all()
    idx = 0
    for tracked in tracking:
        idx += 1
        row = []
        error = False
        request = tracking_to_export_request(tracked)
        for field in fields:
            if field in request:
                row.append(request[field])
            else:
                error = True
                log_writer.writerow([idx, ','.join(row), '%s not a tracking field' % field])
        if not error:
            writer.writerow(row)
            results['total'] += 1
        else:
            results['errors'] += 1

    return True, results


def export_tracking_detail(export_def, writer, log_writer):
    fields = ['id', '', '', 'activty', 'type', 'email_id', 'email_address', 'timestamp']
    objects = []
    results = {'total': 0, 'errors': 0}

    tracking = TrackedCampaign.query.filter(and_(TrackedCampaign.brand_id == export_def.brand_id, TrackedCampaign.id == export_def.target_id)).first()
    if not tracking:
        return False, "Tracking Not Found"

    if tracking.type == 'campaigns':
        status, current_campaign = campaigns.campaign_by_id(export_def.brand_id, tracking.campaign_id)
    elif tracking.type == 'ab_tests':
        status, current_campaign = campaigns.variate_by_id(export_def.brand_id, tracking.campaign_id)
    if not status:
        return False, current_campaign

    fields[1] = '%s_id' % tracking.type[0:-1]
    fields[2] = '%s_name' % tracking.type[0:-1]
    if export_def.target_activity == 'click':
        fields.append('URL')
    writer.writerow(fields)
    
    if export_def.target_type.strip() == '' or export_def.target_type == 'None':
        activity = current_campaign.activity.filter(ListSubscriberActivity.action == export_def.target_activity).all()
    else:
        activity = current_campaign.activity.filter(and_(ListSubscriberActivity.action == export_def.target_activity, ListSubscriberActivity.type == export_def.target_type)).all()
    idx = 0
    for a in activity:
        idx += 1
        row = [tracking.id, tracking.campaign_id, tracking.campaign_name, a.action, a.type, a.list_subscriber.email_id, a.list_subscriber.email_address, a.timestamp]
        if a.action == 'click':
            row.append(a.url)
        writer.writerow(row)
        results['total'] += 1
        
    return True, results

def search(brand, search_type, search_for, search_contains, search_folder_id, search_target_type):
    fields = ["ID", "Campaign", "Email Name", "Subject", "Folder"]
    target_type = search_target_type.replace('_tracking', 's')
    query = TrackedCampaign.query
    if search_for == "campaign_name":
        if search_type == '2':
            query = query.filter(and_(TrackedCampaign.brand_id == brand, TrackedCampaign.type == target_type, TrackedCampaign.folder_id == search_folder_id, TrackedCampaign.campaign_name.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(TrackedCampaign.brand_id == brand, TrackedCampaign.type == target_type, TrackedCampaign.campaign_name.like('%%%s%%' % search_contains)))
    elif search_for == "email_name":
        if search_type == '2':
            query = query.filter(and_(TrackedCampaign.brand_id == brand, TrackedCampaign.type == target_type, TrackedCampaign.folder_id == search_folder_id, TrackedCampaign.email_name.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(TrackedCampaign.brand_id == brand, TrackedCampaign.type == target_type, TrackedCampaign.email_name.like('%%%s%%' % search_contains)))
    elif search_for == "subject_line":
        if search_type == '2':
            query = query.filter(and_(TrackedCampaign.brand_id == brand, TrackedCampaign.type == target_type, TrackedCampaign.folder_id == search_folder_id, TrackedCampaign.subject_line.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(TrackedCampaign.brand_id == brand, TrackedCampaign.type == target_type, TrackedCampaign.subject_line.like('%%%s%%' % search_contains)))
    else:
        return False, "%s not searchable" % search_for

    tracking = query.all()
    rows = []
    for t in tracking:  
        status, folder = folders.get_folder_by_id(brand, folder_id=t.folder_id)
        if not status:
            return False, folder
        row = {}
        row['ID'] = t.id
        row['Campaign'] = '<a href="/tracking/%s/%s/detail">%s</a>' % (target_type, t.id, t.campaign_name)
        row['Email Name'] = t.email_name
        row['Subject'] = t.subject_line
        row['Folder'] = folder.name
        rows.append(row)
    return True, {'Fields': fields, 'Data': rows}

def search_tracking_detail(brand, tracking_id, target_activity, target_type, contains):
    fields = ['Email Address', 'Timestamp']
    data = []

    if target_activity == 'click':
        fields.append('URL')

    status, tracked = tracking_by_id(brand, tracking_id)
    if not status:
        return False, tracked

    if tracked.type == 'campaigns':
        status, current_campaign = campaigns.campaign_by_id(brand, tracked.campaign_id)
    elif tracked.type == 'ab_tests':
        status, current_campaign = campaigns.variate_by_id(brand, tracked.campaign_id)
    if not status:
        return False, current_campaign

    query = current_campaign.activity
    if target_type.strip() != '' and target_type != 'None':
        query = query.filter(and_(ListSubscriberActivity.action == target_activity, ListSubscriberActivity.type == target_type))
    else:
        query = query.filter(ListSubscriberActivity.action == target_activity)
    activity = query.order_by(ListSubscriberActivity.timestamp.desc()).all()

    for a in activity:
        email_address = a.list_subscriber.email_address
        if contains in email_address:
            row = {'Email Address': a.list_subscriber.email_address, 'Timestamp': str(a.timestamp)}
            if a.action == 'click':
                row['URL'] = a.url
            data.append(row)

    return True, {'Fields': fields, 'Data': data}
