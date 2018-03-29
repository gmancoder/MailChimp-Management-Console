from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint, Response
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from sqlalchemy import *
from models.shared import login_manager
from models.users import *
from models.log import *
from models.folders import *
from models.list_subscribers import *
import functions.core as f
import functions.ajax as ajax
import functions.db as dbf
import functions.log as logf
import functions.forms as forms
import functions.emails as em
import functions.lists as lst
import functions.segments as seg
import functions.campaigns as camp
#import functions.tracking as trk
import md5
import urllib2
import urllib
import re
import json
from functools import wraps
import pytz

tracking = Blueprint("tracking", __name__)

DEFAULT_LIST_LENGTH = 25

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@tracking.before_request
def before_request():
    f.Init()
    try:
    	g.folders = Folder.query.filter(and_(Folder.brand_id == g.current_brand.id, Folder.folder_type.in_(['campaign_tracking', 'ab_test_tracking']), Folder.parent_folder_id == None)).order_by(Folder.name.asc()).all()
    	#g.folders = Folder.query.all()
    except Exception as ex:
    	print str(ex)
    return f.CheckPermission()

@tracking.route('/campaign_tracking')
@login_required
def campaign_tracking_redirect():
    return redirect('/tracking/campaigns')

@tracking.route('/ab_test_tracking')
@login_required
def ab_test_tracking_redirect():
    return redirect('/tracking/ab_tests')

from models.tracking import *
@tracking.route('/tracking/<string:type>')
@tracking.route('/tracking/<string:type>/<int:page>')
@login_required
def tracking_index(type="campaigns", page=1):
    query = TrackedCampaign.query.filter(and_(TrackedCampaign.folder_id == g.current_folder.id, TrackedCampaign.type == type))
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
        campaign_tracking = query.paginate(page,r,False).items
    else:
        pages = 0
        campaign_tracking = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(campaign_tracking)))
    return render_template('tracking/tracking.%s.default.html' % type, title="All %s Tracking" % type.title().replace('_', '/'), campaign_tracking=campaign_tracking, pages=pages, current_page=page)

@tracking.route('/tracking/<string:type>/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def tracking_details(type="campaigns", id=None):
    campaign_tracking = TrackedCampaign()
        
    if id != None:
        campaign_tracking = TrackedCampaign.query.filter(and_(TrackedCampaign.brand_id == g.current_brand.id, TrackedCampaign.id == id, TrackedCampaign.type == type)).first()
        if not campaign_tracking:
            msg = 'Tracking Detail not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='View', e_resp="Error", e_resp_msg=msg))
            return redirect('/tracking/%s' % type)
        mode = "update"
        mode_title = campaign_tracking.campaign_name
        log_op = 'Update'
    else:
        msg = 'Tracking Detail not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='View', e_resp="Error", e_resp_msg=msg))
        return redirect('/tracking/%s' % type)
    
    if request.method == 'GET':
        emails = []
        if type == 'campaigns':
            emails.append(campaign_tracking.email_id)
        elif type == 'ab_tests':
            test_type = campaign_tracking.variate_campaign_test_type
            test_combinations = campaign_tracking.variate_campaign_test_combinations
            variate_details = campaign_tracking.variate_campaign_details.all()
            for vd in variate_details:
                email = {'col_size': (12 / test_combinations)}
                email['recipients'] = vd.recipients
                email['is_winner'] = vd.is_winner
                if test_type == 'subject_line':
                    email['email_id'] = campaign_tracking.email_id
                    email['email_name'] = campaign_tracking.email_name
                    email['subject_line'] = vd.subject_line
                    email['from_name'] = campaign_tracking.from_name
                    email['reply_to'] = campaign_tracking.reply_to
                    email['send_time'] = campaign_tracking.send_time
                elif test_type == 'from_name':
                    email['email_id'] = campaign_tracking.email_id
                    email['email_name'] = campaign_tracking.email_name
                    email['subject_line'] = campaign_tracking.subject_line
                    email['from_name'] = vd.from_name
                    email['reply_to'] = vd.reply_to
                    email['send_time'] = campaign_tracking.send_time
                elif test_type == 'send_time':
                    email['email_id'] = campaign_tracking.email_id
                    email['email_name'] = campaign_tracking.email_name
                    email['subject_line'] = campaign_tracking.subject_line
                    email['from_name'] = campaign_tracking.from_name
                    email['reply_to'] = campaign_tracking.reply_to
                    email['send_time'] = vd.send_time
                elif test_type == 'content':
                    email['email_id'] = vd.email_id
                    email['email_name'] = vd.email_name
                    email['subject_line'] = campaign_tracking.subject_line
                    email['from_name'] = campaign_tracking.from_name
                    email['reply_to'] = campaign_tracking.reply_to
                    email['send_time'] = campaign_tracking.send_time
                emails.append(email)

        return render_template('tracking/tracking.%s.properties.html' % type, title=mode_title, update_type=mode, tracked=campaign_tracking, emails=emails)

@tracking.route('/tracking/<string:campaign_type>/<int:id>/<string:activity_type>', methods=['GET'])
@tracking.route('/tracking/<string:campaign_type>/<int:id>/<string:activity_type>/<int:page>', methods=['GET'])
@login_required
def activity_detail(campaign_type, id, activity_type, page=1):
    campaign_tracking = TrackedCampaign()
        
    if id != None:
        campaign_tracking = TrackedCampaign.query.filter(and_(TrackedCampaign.brand_id == g.current_brand.id, TrackedCampaign.id == id, TrackedCampaign.type == campaign_type)).first()
        if not campaign_tracking:
            msg = 'Tracking Detail not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='View', e_resp="Error", e_resp_msg=msg))
            return redirect('/tracking/%s' % campaign_type)
        mode = "update"
        mode_title = campaign_tracking.campaign_name        
        log_op = 'Update'
    else:
        msg = 'Tracking Detail not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='View', e_resp="Error", e_resp_msg=msg))
        return redirect('/tracking/%s' % campaign_type)

    status, current_campaign = camp.campaign_by_id(g.current_brand.id, campaign_tracking.campaign_id)
    if not status:
        msg = 'Campaign not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='View', e_resp="Error", e_resp_msg=msg))
        return redirect('/tracking/%s/%s/detail' % (campaign_type, id))

    query = ListSubscriberActivity.query
    if campaign_type == 'campaigns':
        if 'type' in request.args and request.args.get('type').strip() not in ("", "None"):
            query = query.filter(and_(ListSubscriberActivity.campaign_id == campaign_tracking.campaign_id, ListSubscriberActivity.action == activity_type, ListSubscriberActivity.type == request.args.get('type')))
        else:
            query = query.filter(and_(ListSubscriberActivity.campaign_id == campaign_tracking.campaign_id, ListSubscriberActivity.action == activity_type))
    else:
        if 'type' in request.args and request.args.get('type').strip() not in ("", "None"):
            query = query.filter(and_(ListSubscriberActivity.variate_campaign_id == campaign_tracking.campaign_id, ListSubscriberActivity.action == activity_type, ListSubscriberActivity.type == request.args.get('type')))
        else:
            query = query.filter(and_(ListSubscriberActivity.variate_campaign_id == campaign_tracking.campaign_id, ListSubscriberActivity.action == activity_type))
    query = query.order_by(ListSubscriberActivity.timestamp.desc())

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
        activity_detail = query.paginate(page,r,False).items
    else:
        pages = 0
        activity_detail = query.all()

    return render_template('tracking/tracking.activity.html', title=mode_title, update_type=mode, details=activity_detail, activity=activity_type, id=id, pages=pages, current_page=page, campaign_type=campaign_type, type=request.args.get('type'))
