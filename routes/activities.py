from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint, Response
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from sqlalchemy import *
from models.shared import login_manager
from models.users import *
from models.log import *
from models.folders import *
import functions.core as f
import functions.ajax as ajax
import functions.db as dbf
import functions.log as logf
import functions.forms as forms
import functions.emails as em
import functions.lists as lst
import functions.segments as seg
import functions.campaigns as camp
import md5
import urllib2
import urllib
import re
import json
from functools import wraps
import pytz

activities = Blueprint("activities", __name__)

DEFAULT_LIST_LENGTH = 25

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@activities.before_request
def before_request():
    f.Init()
    try:
    	g.folders = Folder.query.filter(and_(Folder.brand_id == g.current_brand.id, Folder.folder_type.in_(['campaigns', 'ab_tests', 'imports', 'exports']), Folder.parent_folder_id == None)).order_by(Folder.name.asc()).all()
    	#g.folders = Folder.query.all()
    except Exception as ex:
    	print str(ex)
    return f.CheckPermission()

from models.campaigns import *
def _campaign_form(form_campaign, mode, dynamic_attributes, mode_title):
    campaign_form, required_fields = forms.draw_form("campaigns", form_campaign, mode, dynamic_attributes)
    req_fields = '"%s"' % ('","'.join(required_fields))
    return render_template('campaigns/campaigns.properties.html', title=mode_title, update_type=mode, campaign_form=campaign_form, id=dynamic_attributes['id'], status=dynamic_attributes['status'])

@activities.route('/campaigns')
@activities.route('/campaigns/<int:page>')
@login_required
def campaigns(page=1):
    query = Campaign.query.filter(and_(Campaign.type != 'variate', Campaign.folder_id == g.current_folder.id, Campaign.is_user_initiated == False, Campaign.is_rtm == False))
    r = request.args.get('r')
    if not r:
        if 'r' in session:
            r = int(session['r'])
        else:
            r = DEFAULT_LIST_LENGTH
            session['r'] = r
    else:
        r = int(r)
        session['r'] = r
    if r != 0:
        pages = query.count() / r;
        campaigns = query.paginate(page,r,False).items
    else:
        pages = 0
        campaigns = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(campaigns)))
    return render_template('campaigns/campaigns.default.html', title="All campaign", campaigns=campaigns, pages=pages, current_page=page)

@activities.route('/campaigns/new', methods=['GET', 'POST'])
@activities.route('/campaigns/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def campaign_details(id=None):
    dynamic_attributes = {'id': '0', 'status': '', 'campaigns_email_id': {'0': '-Select-'}, 'campaigns_list_id': {'0': '-Select-'}, 'campaigns_segment_id': {'0': '-Select-'}}
    campaign = Campaign()
    campaign.brand_id = g.current_brand.id
    campaign.folder_id = g.current_folder.id
    campaign.inline_css = False
    campaign.auto_footer = False

    mode = "new"
    mode_title = "New campaign"
    log_op = 'Create'
    
    if id != None:
        campaign = Campaign.query.filter(and_(Campaign.brand_id == g.current_brand.id, Campaign.id == id)).first()
        if not campaign:
            msg = 'campaign not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/campaigns')
        mode = "update"
        mode_title = campaign.name
        log_op = 'Update'
        all_segments = seg.all_segments(campaign.brand_id, campaign.list_id)
        for segment in all_segments:
            dynamic_attributes['campaigns_segment_id'][segment['id']] = segment['name']
        dynamic_attributes['id'] = campaign.id
        dynamic_attributes['status'] = campaign.status

        if campaign.status != 'save':
            msg = 'campaign "%s" has been sent, is scheduled to be sent, or is in the process of sending and cannot be edited' % campaign.name
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            return redirect('/campaigns')

    form_campaign = camp.campaign_to_form_request(campaign)
    if request.method == 'POST':
        form_campaign = request.form
        if (mode == "new" and camp.campaign_exists_by_name(g.current_brand.id, form_campaign['campaigns_name'])) or (mode == "update" and campaign.name != form_campaign['campaigns_name'] and camp.campaign_exists_by_name(g.current_brand.id, form_campaign['campaigns_name'])):
            msg = 'campaign with name "%s" already exists' % form_campaign['campaigns_name']
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            _campaign_form(form_campaign, mode, dynamic_attributes, mode_title)
    all_emails = em.all_emails(g.current_brand.id)
    for email in all_emails:
        dynamic_attributes['campaigns_email_id'][email.id] = email.name

    all_lists = lst.get_all(g.current_brand.id)
    for l in all_lists:
        dynamic_attributes['campaigns_list_id'][l.id] = l.name
    
    if request.method == 'GET':
        return _campaign_form(form_campaign, mode, dynamic_attributes, mode_title)

    campaign = camp.request_to_campaign(campaign, request.form)
    campaign.folder_id = g.current_folder.id
    status, response = camp.campaign_to_mailchimp(campaign, mailchimp_id=campaign.mailchimp_id, settings_only=False)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return _campaign_form(form_campaign, mode, dynamic_attributes, mode_title)

    status, response = camp.save_campaign(mode, campaign, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return _campaign_form(form_campaign, mode, dynamic_attributes, mode_title)

    flash("campaign %sd" % log_op, 'info')
    return redirect('/campaigns')

@activities.route('/campaigns/<int:id>/send', methods=['GET', 'POST'])
@login_required
def send_campaign(id):
    campaign = Campaign.query.filter(and_(Campaign.brand_id == g.current_brand.id, Campaign.id == id)).first()
    if not campaign:
        msg = 'Campaign not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Send', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)
    show_test_form = False
    if 'test' in request.args:
        show_test_form = True
    if request.method == 'GET':
       return render_template('campaigns/campaigns.send.html', title="%s - Send campaign" % campaign.name, test=show_test_form, name=campaign.name, referrer=request.referrer)

    referrer = request.form['referrer']
    test = request.form['test']
    test_emails = []
    send_test = False
    if test == '1':
        send_test = True
        test_emails = request.form['test_emails'].split('\n')

    
    status, sendable, checklist = camp.get_send_checklist(campaign.brand_id, campaign.mailchimp_id)
    if not status:
        msg = checklist
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Send", e_resp="Error", e_resp_msg=msg))
        return render_template('campaigns/campaigns.send.html', title="%s - Send campaign" % campaign.name, test=show_test_form, name=campaign.name, referrer=referrer)
    elif not sendable:
        return render_template('campaigns/campaigns.send_not_ready.html', title="%s - campaign is not ready to be sent" % campaign.name, name=campaign.name, send_checklist_items=checklist)
    
    status, response = camp.send_email(campaign.brand_id, campaign.mailchimp_id, send_test, test_emails)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Send", e_resp="Error", e_resp_msg=msg))
        return render_template('campaigns/campaigns.send.html', title="%s - Send campaign" % campaign.name, test=show_test_form, name=campaign.name, referrer=referrer)
    
    if send_test:
        flash('campaign has been test sent', 'info')
    else:
        campaign.status = 'sending'
        status, response = camp.save_campaign('update', campaign, g.user)
        if not status:
            msg = response
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Update", e_resp="Error", e_resp_msg=msg))
            return render_template('campaigns/campaigns.send.html', title="%s - Send campaign" % campaign.name, test=show_test_form, name=campaign.name, referrer=referrer)
        
        flash('campaign has been sent', 'info')
            
    return redirect('/campaigns')

@activities.route('/campaigns/<int:id>/schedule', methods=['GET', 'POST'])
@login_required
def schedule_campaign(id):
    timezone = "US/Eastern"
    campaign_date = datetime.datetime.now()
    campaign_datetime_str = campaign_date.strftime('%Y-%m-%d %I %M %p')
    campaign_datetime_parts = campaign_datetime_str.split(' ')
    campaign_date_str = campaign_datetime_parts[0]
    campaign_minute = campaign_date.minute
    campaign_hour = campaign_date.hour
    while campaign_minute not in (0, 15, 30, 45):
        campaign_minute += 1
        if campaign_minute == 60:
            campaign_hour += 1
            campaign_minute = 0
    campaign_time = '%s:%s %s' % (str(campaign_hour).rjust(2,'0'), str(campaign_minute).rjust(2, '0'), campaign_datetime_parts[3])
    allowed_times = []
    for h_idx in range(0, 24):
        hour = h_idx
        ampm = 'AM'
        if hour > 11:
            ampm = 'PM'
            if hour > 12:
                hour = hour - 12
        elif hour == 0:
            hour = 12
        for m_idx in range(0, 60, 15):
            allowed_times.append('%s:%s %s' % (str(hour).rjust(2, '0'), str(m_idx).rjust(2, '0'), ampm))
    all_timezones = [x for x in pytz.all_timezones if x.startswith('US') or x.startswith('Canada')]
    campaign = Campaign.query.filter(and_(Campaign.brand_id == g.current_brand.id, Campaign.id == id)).first()
    if not campaign:
        msg = 'Campaign not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)

    if request.method == 'GET':
        if campaign.schedule_time != None:
            msg = 'Campaign already scheduled'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
            return redirect(request.referrer)
        
        return render_template('campaigns/campaigns.schedule.html', title='%s - Schedule campaign' % campaign.name, name=campaign.name, campaign_date=campaign_date_str, campaign_time=campaign_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)

    # POST
    status, sendable, checklist = camp.get_send_checklist(campaign.brand_id, campaign.mailchimp_id)

    if not status:
        msg = checklist
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Schedule", e_resp="Error", e_resp_msg=msg))
        return render_template('campaigns/campaigns.schedule.html', title='%s - Schedule campaign' % campaign.name, name=campaign.name, campaign_date=campaign_date_str, campaign_time=campaign_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    elif not sendable:
        return render_template('campaigns/campaigns.send_not_ready.html', title="%s - campaign is not ready to be scheduled" % campaign.name, name=campaign.name, send_checklist_items=checklist)

    campaign_date_str = request.form['campaign_date']
    campaign_time = request.form['campaign_time']
    timezone = request.form['timezone']

    tz = pytz.timezone(timezone)
    campaign_datetime = datetime.datetime.strptime('%s %s' % (campaign_date_str, campaign_time), '%Y-%m-%d %I:%M %p')
    if campaign_datetime <= datetime.datetime.now():
        msg = "Scheduled time must be after current time"
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Schedule", e_resp="Error", e_resp_msg=msg))
        return render_template('campaigns/campaigns.schedule.html', title='%s - Schedule campaign' % campaign.name, name=campaign.name, campaign_date=campaign_date_str, campaign_time=campaign_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    campaign_date = tz.localize(campaign_datetime)
    campaign.status = 'schedule'
    campaign.schedule_time = campaign_date.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    status, response = camp.schedule_campaign(campaign)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return render_template('campaigns/campaigns.schedule.html', title='%s - Schedule campaign' % campaign.name, name=campaign.name, campaign_date=campaign_date_str, campaign_time=campaign_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    
    status, response = camp.save_campaign('update', campaign, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Schedule", e_resp="Error", e_resp_msg=msg))
        return render_template('campaigns/campaigns.schedule.html', title='%s - Schedule campaign' % campaign.name, name=campaign.name, campaign_date=campaign_date_str, campaign_time=campaign_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    
    flash('campaign has been scheduled', 'info')
    return redirect('/campaigns')

@activities.route('/campaigns/<int:id>/unschedule', methods=['GET'])
@login_required
def unschedule_campaign(id):
    campaign = Campaign.query.filter(and_(Campaign.brand_id == g.current_brand.id, Campaign.id == id)).first()
    if not campaign:
        msg = 'Campaign not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)

    campaign.schedule_time = None
    campaign.status = 'save'

    status, response = camp.unschedule_campaign(campaign)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Unschedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)
    
    status, response = camp.save_campaign('update', campaign, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Unschedule", e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)
    
    flash('campaign schedule has been cancelled', 'info')
    return redirect('/campaigns')

@activities.route('/campaigns/<int:id>/replicate', methods=['GET'])
@login_required
def replicate_campaign(id):
    campaign = Campaign.query.filter(and_(Campaign.brand_id == g.current_brand.id, Campaign.id == id)).first()
    if not campaign:
        msg = 'Campaign not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)

    status, response = camp.replicate_campaign(campaign, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)

    flash('campaign has been replicated and new campaign has been saved')
    return redirect('/campaigns')

def _ab_test_form(form_ab_test, mode, dynamic_attributes, mode_title):
    ab_test_form, required_fields = forms.draw_form("ab_tests", form_ab_test, mode, dynamic_attributes)
    req_fields = '"%s"' % ('","'.join(required_fields))
    return render_template('ab_tests/ab_tests.properties.html', title=mode_title, update_type=mode, ab_test_form=ab_test_form, id=dynamic_attributes['id'], status=dynamic_attributes['status'])

@activities.route('/ab_tests')
@activities.route('/ab_tests/<int:page>')
@login_required
def ab_tests(page=1):
    query = VariateCampaign.query.filter(VariateCampaign.folder_id == g.current_folder.id)
    r = request.args.get('r')
    if not r:
        if 'r' in session:
            r = int(session['r'])
        else:
            r = DEFAULT_LIST_LENGTH
            session['r'] = r
    else:
        r = int(r)
        session['r'] = r
    if r != 0:
        pages = query.count() / r;
        ab_tests = query.paginate(page,r,False).items
    else:
        pages = 0
        ab_tests = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(ab_tests)))
    return render_template('ab_tests/ab_tests.default.html', title="All A/B Tests", ab_tests=ab_tests, pages=pages, current_page=page)

@activities.route('/ab_tests/new', methods=['GET', 'POST'])
@activities.route('/ab_tests/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def ab_test_details(id=None):
    dynamic_attributes = {'id': '0', 'status': '', 'ab_tests_list_id': {'0': '-Select-'}, 'ab_tests_segment_id': {'0': '-Select-'}, 'ab_tests_email_id_1': {'0': '-Select-'}, 'ab_tests_email_id_2': {'0': '-Select-'}, 'ab_tests_email_id_3': {'0': '-Select-'}, 'ab_tests_send_time_1': {}, 'ab_tests_send_time_2': {}, 'ab_tests_send_time_3': {}}
    ab_test = VariateCampaign()
    ab_test.brand_id = g.current_brand.id
    ab_test.folder_id = g.current_folder.id

    mode = "new"
    mode_title = "New A/B Test"
    log_op = 'Create'
    
    if id != None:
        ab_test = VariateCampaign.query.filter(and_(VariateCampaign.brand_id == g.current_brand.id, VariateCampaign.id == id)).first()
        if not ab_test:
            msg = 'A/B Test not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/ab_tests')
        mode = "update"
        mode_title = ab_test.name
        log_op = 'Update'
        all_segments = seg.all_segments(ab_test.brand_id, ab_test.list_id)
        for segment in all_segments:
            dynamic_attributes['ab_tests_segment_id'][segment.id] = segment.name
        dynamic_attributes['id'] = ab_test.id
        dynamic_attributes['status'] = ab_test.status

        if ab_test.status != 'save':
            msg = 'A/B Test "%s" has been sent, is scheduled to be sent, or is in the process of sending and cannot be edited' % ab_test.name
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            return redirect('/ab_tests')
    
    form_ab_test = camp.variate_to_form_request(ab_test)
    if request.method == 'POST':
        form_ab_test = request.form
        if (mode == "new" and camp.variate_exists_by_name(g.current_brand.id, form_ab_test['ab_tests_name'])) or (mode == "update" and ab_test.name != form_ab_test['ab_tests_name'] and camp.variate_exists_by_name(g.current_brand.id, form_ab_test['ab_tests_name'])):
            msg = 'ab_test with name "%s" already exists' % form_ab_test['ab_tests_name']
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            _ab_test_form(form_ab_test, mode, dynamic_attributes, mode_title)
    
    all_emails = em.all_emails(g.current_brand.id)
    for email in all_emails:
        dynamic_attributes['ab_tests_email_id_1'][email.id] = email.name
        dynamic_attributes['ab_tests_email_id_2'][email.id] = email.name
        dynamic_attributes['ab_tests_email_id_3'][email.id] = email.name

    for h_idx in range(0, 24):
        hour = h_idx
        ampm = 'AM'
        if hour > 11:
            ampm = 'PM'
            if hour > 12:
                hour = hour - 12
        elif hour == 0:
            hour = 12
        for m_idx in range(0, 60, 15):
            send_time = '%s:%s %s' % (str(hour).rjust(2, '0'), str(m_idx).rjust(2, '0'), ampm)
            dynamic_attributes['ab_tests_send_time_1'][send_time] = send_time
            dynamic_attributes['ab_tests_send_time_2'][send_time] = send_time
            dynamic_attributes['ab_tests_send_time_3'][send_time] = send_time

    all_lists = lst.get_all(g.current_brand.id)
    for l in all_lists:
        dynamic_attributes['ab_tests_list_id'][l.id] = l.name

    if request.method == 'GET':
         return _ab_test_form(form_ab_test, mode, dynamic_attributes, mode_title)

    ab_test = camp.request_to_variate(ab_test, request.form)

    status, response = camp.variate_to_mailchimp(ab_test, mailchimp_id=ab_test.mailchimp_id, settings_only=False)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return _ab_test_form(form_ab_test, mode, dynamic_attributes, mode_title)

    status, response = camp.save_campaign(mode, ab_test, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return _ab_test_form(form_ab_test, mode, dynamic_attributes, mode_title)

    flash("A/B Test %sd" % log_op, 'info')
    return redirect('/ab_tests')

@activities.route('/ab_tests/<int:id>/send', methods=['GET', 'POST'])
@login_required
def send_variate(id):
    variate = VariateCampaign.query.filter(and_(VariateCampaign.brand_id == g.current_brand.id, VariateCampaign.id == id)).first()
    if not variate:
        msg = 'A/B Test not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Send', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)
    if request.method == 'GET':
       return render_template('ab_tests/ab_tests.send.html', title="%s - Begin A/B Test" % variate.name, name=variate.name, referrer=request.referrer)

    referrer = request.form['referrer']
    status, sendable, checklist = camp.get_send_checklist(variate.brand_id, variate.mailchimp_id)
    if not status:
        msg = checklist
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Send", e_resp="Error", e_resp_msg=msg))
        return render_template('ab_tests/ab_tests.send.html', title="%s - Begin A/B Test" % variate.name, test=show_test_form, name=variate.name, referrer=referrer)
    elif not sendable:
        return render_template('ab_tests/ab_tests.send_not_ready.html', title="%s - A/B Test is not ready to be sent" % variate.name, name=variate.name, send_checklist_items=checklist)
    
    status, response = camp.send_email(variate.brand_id, variate.mailchimp_id)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Send", e_resp="Error", e_resp_msg=msg))
        return render_template('ab_tests/ab_tests.send.html', title="%s - Begin A/B Test" % variate.name, test=show_test_form, name=variate.name, referrer=referrer)
    
    variate.status = 'sending'
    status, response = camp.save_campaign('update', variate, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Update", e_resp="Error", e_resp_msg=msg))
        return render_template('ab_tests/ab_tests.send.html', title="%s - Begin A/B Test" % variate.name, test=show_test_form, name=variate.name, referrer=referrer)
        
        flash('A/B Test has begun', 'info')
            
    return redirect('/ab_tests')

@activities.route('/ab_tests/<int:id>/schedule', methods=['GET', 'POST'])
@login_required
def schedule_variate(id):
    timezone = "US/Eastern"
    variate_date = datetime.datetime.now()
    variate_datetime_str = variate_date.strftime('%Y-%m-%d %I %M %p')
    variate_datetime_parts = variate_datetime_str.split(' ')
    variate_date_str = variate_datetime_parts[0]
    variate_minute = variate_date.minute
    while variate_minute not in (0, 15, 30, 45):
        variate_minute += 1
    variate_time = '%s:%s %s' % (variate_datetime_parts[1], str(variate_minute).rjust(2, '0'), variate_datetime_parts[3])
    allowed_times = []
    for h_idx in range(0, 24):
        hour = h_idx
        ampm = 'AM'
        if hour > 11:
            ampm = 'PM'
            if hour > 12:
                hour = hour - 12
        elif hour == 0:
            hour = 12
        for m_idx in range(0, 60, 15):
            allowed_times.append('%s:%s %s' % (str(hour).rjust(2, '0'), str(m_idx).rjust(2, '0'), ampm))
    all_timezones = [x for x in pytz.all_timezones if x.startswith('US') or x.startswith('Canada')]
    variate = VariateCampaign.query.filter(and_(VariateCampaign.brand_id == g.current_brand.id, VariateCampaign.id == id)).first()
    if not variate:
        msg = 'A/B Test not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)

    if request.method == 'GET':
        if variate.schedule_time != None:
            msg = 'A/B Test already scheduled'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
            return redirect(request.referrer)
        
        return render_template('ab_tests/ab_tests.schedule.html', title='%s - Schedule A/B Test' % variate.name, name=variate.name, variate_date=variate_date_str, variate_time=variate_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)

    # POST
    status, sendable, checklist = camp.get_send_checklist(variate.brand_id, variate.mailchimp_id)

    if not status:
        msg = checklist
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Schedule", e_resp="Error", e_resp_msg=msg))
        return render_template('ab_tests/ab_tests.schedule.html', title='%s - Schedule A/B Test' % variate.name, name=variate.name, variate_date=variate_date_str, variate_time=variate_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    elif not sendable:
        return render_template('ab_tests/ab_tests.send_not_ready.html', title="%s - A/B Test is not ready to be scheduled" % variate.name, name=variate.name, send_checklist_items=checklist)

    variate_date_str = request.form['variate_date']
    variate_time = request.form['variate_time']
    timezone = request.form['timezone']

    tz = pytz.timezone(timezone)
    variate_datetime = datetime.datetime.strptime('%s %s' % (variate_date_str, variate_time), '%Y-%m-%d %I:%M %p')
    if variate_datetime <= datetime.datetime.now():
        msg = "Scheduled time must be after current time"
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Schedule", e_resp="Error", e_resp_msg=msg))
        return render_template('ab_tests/ab_tests.schedule.html', title='%s - Schedule A/B Test' % variate.name, name=variate.name, variate_date=variate_date_str, variate_time=variate_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    variate_date = tz.localize(variate_datetime)
    variate.status = 'schedule'
    variate.schedule_time = variate_date.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    status, response = camp.schedule_campaign(variate)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return render_template('ab_tests/ab_tests.schedule.html', title='%s - Schedule A/B Test' % variate.name, name=variate.name, variate_date=variate_date_str, variate_time=variate_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    
    status, response = camp.save_campaign('update', variate, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Schedule", e_resp="Error", e_resp_msg=msg))
        return render_template('ab_tests/ab_tests.schedule.html', title='%s - Schedule A/B Test' % variate.name, name=variate.name, variate_date=variate_date_str, variate_time=variate_time, timezone=timezone, referrer=request.referrer, times=allowed_times, timezones=all_timezones)
    
    flash('A/B Test has been scheduled', 'info')
    return redirect('/ab_tests')

@activities.route('/ab_tests/<int:id>/unschedule', methods=['GET'])
@login_required
def unschedule_variate(id):
    variate = VariateCampaign.query.filter(and_(VariateCampaign.brand_id == g.current_brand.id, VariateCampaign.id == id)).first()
    if not variate:
        msg = 'A/B Test not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Schedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)

    variate.schedule_time = None
    variate.status = 'save'

    status, response = camp.unschedule_campaign(variate)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Unschedule', e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)
    
    status, response = camp.save_campaign('update', variate, g.user)
    if not status:
        msg = response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op="Unschedule", e_resp="Error", e_resp_msg=msg))
        return redirect(request.referrer)
    
    flash('A/B Test schedule has been cancelled', 'info')
    return redirect('/ab_tests')

from models.imports import *
@activities.route('/imports')
@activities.route('/imports/<int:page>')
@login_required
def imports(page=1):
    query = ImportDefinition.query.filter(and_(ImportDefinition.folder_id == g.current_folder.id, ImportDefinition.system_definition == False, ImportDefinition.brand_id == g.current_brand.id))
    r = request.args.get('r')
    q = request.args.get('q')
    if not q:
        q = "";
    if not r:
        if 'r' in session:
            r = int(session['r'])
        else:
            r = DEFAULT_LIST_LENGTH
            session['r'] = r
    else:
        r = int(r)
        session['r'] = r
    if r != 0:
        pages = query.count() / r;
        if q:
            imports = query.filter(ImportDefinition.name.like('%%%s%%' % q)).order_by(ImportDefinition.name).paginate(page, r, False).items
        else:
            imports = query.order_by(ImportDefinition.name).paginate(page,r,False).items
    else:
        pages = 0
        if q:
            imports = query.filter(ImportDefinition.name.like('%%%s%%' % q)).order_by(ImportDefinition.name).all()
        else:
            imports = query.order_by(ImportDefinition.name).all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(imports)))
    return render_template('imports/imports.default.html', title="All Import", imports=imports, pages=pages, current_page=page, rows=r, q=q)

@activities.route('/imports/new', methods=['GET', 'POST'])
@activities.route('/imports/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def import_details(id=None):
    import_definition = ImportDefinition()
    import_definition.name = ""
    import_definition.file_path = ""
    
    import_definition.system_definition = False;
    import_definition.brand_id = g.current_brand.id
    import_definition.folder_id = g.current_folder.id
    import_definition.file_delimiter = ','
    import_definition.import_type = 1
    import_definition.notify_addresses = g.user.email

    mode = "new"
    mode_title = "New Import"
    log_op = 'Create'
    
    if id != None:
        import_definition = ImportDefinition.query.filter(and_(Import.brand_id == g.current_brand.id, Import.id == id)).first()
        if not import_definition:
            msg = 'Import Definition not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/imports')
        mode = "update"
        mode_title = import_definition.name
        log_op = 'Update'
    
    if request.method == 'GET':
        return render_template('imports/imports.properties.html', title=mode_title, update_type=mode, import_definiton=import_definition)