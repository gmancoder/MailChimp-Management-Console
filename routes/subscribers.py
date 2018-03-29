from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint, Response
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from sqlalchemy import *
from models.shared import login_manager
from models.users import *
from models.log import *
from models.list_subscribers import *
from models.lists import *
from models.folders import *
import functions.core as f
import functions.ajax as ajax
import functions.db as dbf
import functions.log as logf
import functions.forms as forms
import functions.lists as lst
import md5
import urllib2
import re
import json
from functools import wraps

subscribers = Blueprint("subscribers", __name__)

DEFAULT_LIST_LENGTH = 25

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@subscribers.before_request
def before_request():
    f.Init()
    try:
        #print "BEFORE REQUEST"
    	g.folders = Folder.query.filter(and_(Folder.brand_id == g.current_brand.id, Folder.folder_type.in_(['lists', 'segments']), Folder.parent_folder_id == None)).order_by(Folder.name.asc()).all()
    	#print len(g.folders)
        #g.folders = Folder.query.all()
        #print g.folders
    except Exception as ex:
    	print str(ex)
    return f.CheckPermission()
#@subscribers.route("/subscribers")
#@login_required
#def subscribers():
#	subscribers = {}
#	all_subscribers = ListSubscriber.query.filter(ListSubscriber.brand_id == g.current_brand.id).order_by(ListSubscriber.unique_email_id.asc(), ListSubscriber.created.asc()).all()
#	for sub in all_subscribers:
#		if sub.unique_email_id not in subscribers:
#			subscribers[sub.unique_email_id] = {'EmailAddress': sub.email_address, 'SubscriberID': sub.unique_email_id, 'Status': sub.status, 'DateCreated': sub.created, 'DateUnsub': ''}

@subscribers.route('/lists')
@subscribers.route('/lists/<int:page>')
@login_required
def lists(page=1):
    query = List.query.filter(List.folder_id == g.current_folder.id)
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
        lists = query.paginate(page,r,False).items
    else:
        pages = 0
        lists = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(lists)))
    return render_template('lists/lists.default.html', title="Lists", lists=lists, pages=pages, current_page=page)

@subscribers.route('/lists/new', methods=['GET', 'POST'])
@login_required
def new_list():
    if request.method == "GET":
        return _render_list_properties_form({}, "new", "New List")
    else:
        valid, violating_field = lst.check_fields_in_add_request(request.form)
        if not valid:
            msg = 'Missing Field "%s"' % violating_field
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_list_properties_form(request.form, "new", "New List")
        status, mc_resp = lst.post_list_to_mailchimp(g.current_brand, request.form)
        if not status:
            msg = 'MailChimp Create Failed: %s' % mc_resp
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_list_properties_form(request.form, "new", "New List")
        else:
            mc = json.loads(mc_resp)
            mc_id = mc['id']
            status, resp = lst.post_list_to_database(g.current_brand, mc_id, g.current_folder.id, request.form, g.user)
            if status:
                msg = "List %s created successfully" % resp['Name']
                logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="OK", e_resp_msg=msg))
                flash(msg, 'message')
                return redirect("/lists")
            else:
                msg = 'DB Create Failed: %s' % resp
                logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
                flash(msg, 'error')
                return _render_list_properties_form(request.form, "new", "New List")

@subscribers.route("/lists/<int:id>/properties", methods=['GET', 'POST'])
@login_required
def properties(id):
    list_props = List.query.get(id)
    if not list_props:
        msg = "List not found"
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Properties', e_resp="Error", e_resp_msg=msg))
        flash(msg, "error")
        return redirect("/lists")

    if request.method == "GET":
        props = lst.list_to_request(list_props)
        return _render_list_properties_form(props, "update", list_props.name)
    else:
        valid, violating_field = lst.check_fields_in_update_request(request.form)
        if not valid:
            msg = 'Missing Field "%s"' % violating_field
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Properties', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_list_properties_form(request.form, "update", list_props.name)
        status, mc_resp = lst.patch_list_to_mailchimp(g.current_brand, list_props.mailchimp_id, request.form)
        if not status:
            msg = 'MailChimp Update Failed: %s' % mc_resp
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Properties', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_list_properties_form(request.form, "update", list_props.name)
        else:
            status, resp = lst.patch_list_to_database(request.form, g.user, id, list_props.mailchimp_id)
            if status:
                msg = "List %s updated successfully" % resp['Name']
                logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Properties', e_resp="OK", e_resp_msg=msg))
                flash(msg, 'message')
                return redirect("/lists")
            else:
                msg = 'DB Update Failed: %s' % resp
                logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Properties', e_resp="Error", e_resp_msg=msg))
                flash(msg, 'error')
                return _render_list_properties_form(request.form, "new", list_props.name)

@subscribers.route('/lists/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def details(id):
    current_list = List.query.get(id)
    if not current_list:
        msg = "List '%s' not found" % id
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Details', e_resp="Error", e_resp_msg=msg))
        flash(msg, 'error')
        return redirect("/lists")

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Properties', e_resp="OK", e_resp_msg=""))
    return render_template('lists/lists.details.html', title='%s Details' % current_list.name, current_list=current_list, country_list=forms.create_country_dict())

def _render_list_properties_form(f, form_type, title):
    form, required_fields = forms.draw_form("lists", f, form_type)
    req_fields = '"%s"' % ('","'.join(required_fields))
    return render_template('lists/lists.properties.html', title=title, form=form, required=req_fields)

@subscribers.route('/subscribers/<int:id>', methods=['GET', 'POST'])
@login_required
def subscriber_details(id):
    
    subscriber = ListSubscriber.query.get(id)
    if not subscriber:
        msg = "Subscriber '%s' not found" % id
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Details', e_resp="Error", e_resp_msg=msg))
        flash(msg, 'error')
        return redirect("/subscribers")
    current_list = List.query.get(subscriber.list_id)
    if not current_list:
        msg = "List '%s' not found" % subscriber.list_id
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Details', e_resp="Error", e_resp_msg=msg))
        flash(msg, 'error')
        return redirect("/subscribers")
    segments = seg.subscriber_segments(g.current_brand.id, id)
    list_merge_fields = current_list.merge_fields.order_by(ListMergeField.display_order.asc()).all()
    current_folder = Folder.query.get(current_list.folder_id)
    subscriber_location = subscriber.location.first()
    subscriber_dict = lst.process_subscriber(subscriber, list_merge_fields)

    if request.method == "GET":
        refer = request.referrer
        return render_template('subscribers/subscribers.details.html', refer=refer, segments=segments, title="Subscriber Details", current_list=current_list, subscriber=subscriber_dict, merge_fields=list_merge_fields, current_folder=current_folder, new=False, subscriber_location=subscriber_location, activity=subscriber.activity.all())
    else:
        refer = request.form['refer']
        subscriber_dict["Status"] = request.form['status']
        subscriber_dict["EmailTypePreference"] = request.form['email_type']
        subscriber_merge_fields = {}
        validation_errors = 0
        for merge_field in list_merge_fields:
            if merge_field.tag not in request.form and merge_field.required:
                validation_errors += 1
            else:
                subscriber_merge_fields[merge_field.id] = request.form[merge_field.tag]
                subscriber_dict[merge_field.tag] = request.form[merge_field.tag]
        subscriber_dict['location'] = {}
        subscriber_dict['location']['latitude'] = request.form['latitude']
        subscriber_dict['location']['longitude'] = request.form['longitude']
        if validation_errors > 0:
            msg = "%d validation errors occurred. Please check form and try again"
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('subscribers/subscribers.details.html', refer=refer, segments=segments, title="Subscriber Details", current_list=current_list, subscriber=subscriber_dict, merge_fields=list_merge_fields, current_folder=current_folder, new=False, subscriber_location=subscriber_location, activity=subscriber.activity.all())
        status, response = lst.update_subscriber_to_mailchimp(current_list, list_merge_fields, subscriber_dict, subscriber.email_id)
        if not status:
            msg = 'Mailchimp Update Failed: %s' % response
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('subscribers/subscribers.details.html', refer=refer, segments=segments, title="Subscriber Details", current_list=current_list, subscriber=subscriber_dict, merge_fields=list_merge_fields, current_folder=current_folder, new=False, subscriber_location=subscriber_location, activity=subscriber.activity.all())
        
        mailchimp_response = json.loads(response)
        location = mailchimp_response['location']
        last_changed = mailchimp_response['last_changed']

        status, response = lst.update_subscriber_to_db(subscriber.id, subscriber_dict["EmailTypePreference"], subscriber_dict["Status"], last_changed, location, subscriber_merge_fields, g.user)
        if not status:
            msg = 'DB Update Failed: %s' % response
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Add', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('subscribers/subscribers.details.html', refer=refer, segments=segments, title="Subscriber Details", current_list=current_list, subscriber=subscriber_dict, merge_fields=list_merge_fields, current_folder=current_folder, new=False, subscriber_location=subscriber_location, activity=subscriber.activity.all())
        
        return redirect(refer)

@subscribers.route('/subscribers/<int:list_id>/add', methods=['GET', 'POST'])
@login_required
def new_subscriber(list_id):
    current_list = List.query.get(list_id)
    if not current_list:
        msg = "List '%s' not found" % list_id
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Add', e_resp="Error", e_resp_msg=msg))
        flash(msg, 'error')
        return redirect("/subscribers")
    list_merge_fields = current_list.merge_fields.order_by(ListMergeField.display_order.asc()).all()
    current_folder = Folder.query.get(current_list.folder_id)
    if request.method == "GET":
        sub = {'ID': 0, 'EmailAddress': "New Subscriber", 'Status': "pending", 'EmailTypePreference': "html"}
        sub = lst.process_subscriber_merge_fields(sub, list_merge_fields)
        return render_template('subscribers/subscribers.details.html', title="Create New Subscriber", current_list=current_list, subscriber=sub, merge_fields=list_merge_fields, current_folder=current_folder, new=True, subscriber_location=None)
    else:
        email_address = request.form['email_address']
        email_type = request.form['email_type']
        email_status = request.form['status']
        new_subscriber = {'ID': 0, 'EmailAddress': email_address, 'EmailTypePreference': email_type, 'Status': email_status}
        subscriber_merge_fields = {}
        validation_errors = 0
        for merge_field in list_merge_fields:
            if merge_field.tag not in request.form and merge_field.required:
                validation_errors += 1
            else:
                subscriber_merge_fields[merge_field.tag] = request.form[merge_field.tag]
                new_subscriber[merge_field.tag] = request.form[merge_field.tag]
        new_subscriber['location'] = {}
        new_subscriber['location']['latitude'] = request.form['latitude']
        new_subscriber['location']['longitude'] = request.form['longitude']
        if validation_errors > 0:
            msg = "%d validation errors occurred. Please check form and try again"
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Add', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('subscribers/subscribers.details.html', title="Create New Subscriber", current_list=current_list, subscriber=new_subscriber, merge_fields=list_merge_fields, current_folder=current_folder, new=True, subscriber_location=None, activity=[])

        status, response = lst.add_subscriber_to_mailchimp(current_list, list_merge_fields, new_subscriber)
        if not status:
            msg = 'Mailchimp Add Failed: %s' % response
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Add', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('subscribers/subscribers.details.html', title="Create New Subscriber", current_list=current_list, subscriber=new_subscriber, merge_fields=list_merge_fields, current_folder=current_folder, new=True, subscriber_location=None, activity=[])
        
        mailchimp_response = json.loads(response)
        #print mailchimp_response
        email_id = mailchimp_response['id']
        unique_email_id = mailchimp_response['unique_email_id']
        timestamp_signup = mailchimp_response['timestamp_opt']
        location = mailchimp_response['location']
        last_changed = mailchimp_response['last_changed']

        status, response = lst.add_subscriber_to_db(current_list.brand_id, current_list.id, email_id, email_address, unique_email_id, email_type, email_status, timestamp_signup, last_changed, location, subscriber_merge_fields, g.user)
        if not status:
            msg = 'DB Add Failed: %s' % response
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Add', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('subscribers/subscribers.details.html', title="Create New Subscriber", current_list=current_list, subscriber=new_subscriber, merge_fields=list_merge_fields, current_folder=current_folder, new=True, subscriber_location=None, activity=[])
        return redirect('/lists/%s/detail' % current_list.id)

from models.segments import *
import functions.segments as seg
@subscribers.route('/segments')
@subscribers.route('/segments/<int:page>')
@login_required
def segments(page=1):
    query = Segment.query.filter(Segment.folder_id == g.current_folder.id)
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
        segments = query.paginate(page,r,False).items
    else:
        pages = 0
        segments = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(segments)))
    return render_template('segments/segments.default.html', title="All Segment", segments=segments, pages=pages, current_page=page)

@subscribers.route('/segments/new', methods=['GET', 'POST'])
@subscribers.route('/segments/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def segment_details(id=None):
    segment = Segment()
    mode = "new"
    mode_title = "New Segment"
    log_op = 'Create'
    static_subscriber_ids = []
    segment_conditions = []
    static_subscribers = []

    # Lists
    current_lists = lst.get_all(g.current_brand.id)
    all_lists = {}
    for current_list in current_lists:
        all_lists[current_list.id] = current_list.name
    additional_objects = {'segments_list_id': all_lists}

    if id != None:
        segment = Segment.query.filter(and_(Segment.brand_id == g.current_brand.id, Segment.id == id)).first()
        if not segment:
            msg = 'Segment not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/segments')
        mode = "update"
        mode_title = segment.name
        log_op = 'Update'
        segment_conditions = segment.conditions.all()
        for subscriber in segment.subscribers.all():
            static_subscriber_ids.append(subscriber.id)
            static_subscribers.append(subscriber.email_address)

    segment_dict = seg.segment_to_form_dict(segment)
    if request.method == 'POST':
        segment_dict = request.form
    form, required_fields = forms.draw_form("segments", segment_dict, mode, additional_objects)
    
    if request.method == 'GET':
        return render_template('segments/segments.properties.html', title=mode_title, update_type=mode, form=form, required_fields=required_fields, conditions=segment_conditions, subscribers=static_subscriber_ids, id=id, type=segment.type)

    list_id = request.form['segments_list_id']
    name = request.form['segments_name']
    match = request.form['segments_match']
    type = request.form['segments_type']
    if type == 'saved':
        conditions = request.form.getlist('segment_condition')
        for condition in conditions:
            segment_conditions.append(seg.segment_condition_from_string(condition))
    elif type == 'static':
        subscribers = request.form['selected_subscribers'].split(';')
        print subscribers
        for subscriber in subscribers:
            if subscriber.strip() != "":
                static_subscriber = subscriber.split('|')
                static_subscriber_ids.append(static_subscriber[0])
                static_subscribers.append(static_subscriber[1])

    status, response = seg.segment_to_mailchimp(g.current_brand.id, list_id, name, match, segment_conditions, static_subscribers, segment.mailchimp_id)
    if not status:
        msg = 'Mailchimp %s FAILED - %s' % (log_op, response)
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return render_template('segments/segments.properties.html', title=mode_title, update_type=mode, form=form, required_fields=required_fields, conditions=segment_conditions, subscribers=static_subscriber_ids, id=id, type=segment.type)
    
    mailchimp_id = segment.mailchimp_id
    type = segment.type
    if mailchimp_id == None:
        j_response = json.loads(response)
        mailchimp_id = j_response['id']
        type = j_response['type']
    
    status, response = seg.segment_to_db(g.current_brand.id, g.current_folder.id, mailchimp_id, name, type, match, g.user, segment_conditions, list_id=list_id, id=id)
    if not status:
        msg = 'DB %s FAILED - %s' % (log_op, response)
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return render_template('segments/segments.properties.html', title=mode_title, update_type=mode, form=form, required_fields=required_fields, conditions=segment_conditions, subscribers=static_subscriber_ids, id=id, type=segment.type)
    if (len(response) > 0 and 'id' in response[0]):
        if id == None:
            id = response[0]['id']
    status, response = seg.apply_segment_subscribers_from_mailchimp(g.current_brand.id, id)
    if not status:
        msg = 'Getting Subscribers FAILED - %s' % response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return render_template('segments/segments.properties.html', title=mode_title, update_type=mode, form=form, required_fields=required_fields, conditions=segment_conditions, subscribers=static_subscriber_ids, id=id, type=segment.type)

    flash('Segment created successfully', 'info')
    if id != None:
        return redirect('/segments/%s/detail' % id)
    else:
        return redirect('/segments')