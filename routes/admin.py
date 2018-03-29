import os
import sys
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from models.shared import login_manager
from models.tools import *
from models.log import *
import functions.core as f
import functions.log as logf
import functions.tools as tls
import functions.brands as brands
import functions.activities as act
import functions.file_locations as fl
import md5
import datetime
import inflection

admin = Blueprint("admin", __name__)
DEFAULT_LIST_LENGTH = 25

@admin.before_request
def before_request():
    f.Init()
    #return f.CheckPermission()

from models.forms import *
@admin.route('/admin/forms')
@admin.route('/admin/forms/<int:page>')
@login_required
def forms(page=1):
    query = Form.query.filter(Form.folder_id == g.current_folder.id)
    r = request.args.get('r')
    q = request.args.get('q')
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
            forms = query.filter(Form.name.like('%%%s%%' % q)).order_by(Form.name).paginate(page, r, False).items
        else:
            forms = query.order_by(Form.name).paginate(page,r,False).items
    else:
        pages = 0
        if q:
            forms = query.filter(Form.name.like('%%%s%%' % q)).order_by(Form.name).all()
        else:
            forms = query.order_by(Form.name).all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(forms)))
    return render_template('forms/forms.default.html', title="All Form", forms=forms, pages=pages, current_page=page)

@admin.route('/admin/forms/new', methods=['GET', 'POST'])
@admin.route('/admin/forms/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def form_details(id=None):
    form = Form()
    mode = "new"
    mode_title = "New Form"
    log_op = 'Create'
    
    if id != None:
        form = Form.query.filter(and_(Form.brand_id == g.current_brand.id, Form.id == id)).first()
        if not form:
            msg = 'Form not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/forms')
        mode = "update"
        mode_title = form.name
        log_op = 'Update'
    
    if request.method == 'GET':
        return render_template('forms/forms.properties.html', title=mode_title, update_type=mode, form=form)

from models.system_jobs import *
@admin.route('/admin/system_jobs')
@admin.route('/admin/system_jobs/<int:page>')
@login_required
def system_jobs(page=1):
    query = SystemJob.query
    r = request.args.get('r')
    q = request.args.get('q')
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
        system_jobs = query.order_by(SystemJob.start_date.desc()).paginate(page,r,False).items
    else:
        pages = 0
        system_jobs = query.order_by(SystemJob.start_date.desc()).all()

    jobs_list = []
    for job in system_jobs:
        brand = brands.brand_by_id(job.brand_id)
        if not brand:
            continue

        if not q or q in brand.client:
            if job.activity_type == 'imports':
                import_def = act.get_import_definition(job.activity_id)
                if not import_def:
                    continue
                name = import_def.name
            elif job.activity_type == 'exports':
                export_def = act.get_export_definition(job.activity_id)
                if not export_def:
                    continue
                name = export_def.name
            elif job.activity_type == 'tracking_exports':
                tracking_export_def = act.get_tracking_export_definition(job.activity_id)
                if not tracking_export_def:
                    continue
                name = tracking_export_def.name
            elif job.activity_type == "file_transfers":
                name = "File Transfer %s" % job.activity_id
            else:
                name = '%s %s' % (inflection.titleize(job.activity_type), job.activity_id)

            if not q or q in name:
                jobs_list.append({'Name': name, 'Brand': brand.client, 'Type': inflection.titleize(job.activity_type), 'Job': job})

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(system_jobs)))
    return render_template('system_jobs/system_jobs.default.html', title="All System Jobs", system_jobs=jobs_list, pages=pages, current_page=page, rows=r, q=q)

@admin.route('/admin/system_jobs/<int:id>/detail', methods=['GET'])
@login_required
def system_job_details(id=None):
    system_job = SystemJob()
    mode = "new"
    mode_title = "New SystemJob"
    log_op = 'Create'
    
    if id != None:
        system_job = SystemJob.query.get(id)
        if not system_job:
            msg = 'System Job not found'
            return system_job_detail_error(msg)
        mode = "update"
        brand = brands.brand_by_id(system_job.brand_id)
        if not brand:
            msg = 'Brand not found'
            return system_job_detail_error(msg)
        if system_job.activity_type == 'imports':
            import_def = act.get_import_definition(system_job.activity_id)
            if not import_def:
                msg = 'Import Definition not found'
                return system_job_detail_error(msg)
            name = import_def.name
        elif system_job.activity_type == 'exports':
            export_def = act.get_export_definition(system_job.activity_id)
            if not export_def:
                msg = 'Export Definition not found'
                return system_job_detail_error(msg)
            name = export_def.name
        elif system_job.activity_type == 'tracking_exports':
            tracking_export_def = act.get_tracking_export_definition(system_job.activity_id)
            if not tracking_export_def:
                msg = 'Tracking Export Definition not found'
                return system_job_detail_error(msg)
            name = tracking_export_def.name
        elif system_job.activity_type == "file_transfers":
            name = "File Transfer %s" % system_job.activity_id
        else:
            name = '%s %s' % (inflection.titleize(job.activity_type), system_job.activity_id)
        mode_title = name
        log_op = 'Update'

        return render_template('system_jobs/system_jobs.properties.html', title=mode_title, update_type=mode, system_job=system_job, name=name, type=inflection.titleize(system_job.activity_type), brand=brand)

def system_job_detail_error(msg):
    flash(msg, 'error')
    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
    return redirect('/admin/system_jobs')

from models.file_locations import *
@admin.route('/admin/file_locations')
@admin.route('/admin/file_locations/<int:page>')
@login_required
def file_locations(page=1):
    query = FileLocation.query
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
            file_locations = query.filter(FileLocation.name.like('%%%s%%' % q)).order_by(FileLocation.name).paginate(page, r, False).items
        else:
            file_locations = query.order_by(FileLocation.name).paginate(page,r,False).items
    else:
        pages = 0
        if q:
            file_locations = query.filter(FileLocation.name.like('%%%s%%' % q)).order_by(FileLocation.name).all()
        else:
            file_locations = query.order_by(FileLocation.name).all()
    file_locations_list = []
    for file_location in file_locations:
        brand = brands.brand_by_id(file_location.brand_id)
        file_locations_list.append({'FL': file_location, 'Brand': brand})
    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(file_locations)))
    return render_template('file_locations/file_locations.default.html', title="All File Locations", file_locations=file_locations_list, pages=pages, current_page=page, rows=r, q=q)

@admin.route('/admin/file_locations/new', methods=['GET', 'POST'])
@admin.route('/admin/file_locations/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def file_location_details(id=None):
    file_location = FileLocation()
    file_location.name = ""
    mode = "new"
    mode_title = "New File Location"
    log_op = 'Create'

    brand_list = brands.all_brands()
    
    if id != None:
        file_location = FileLocation.query.get(id)
        if not file_location:
            msg = 'File Location not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/admin/file_locations')
        mode = "update"
        mode_title = file_location.name
        log_op = 'Update'

    if request.method == 'GET':
        return render_template('file_locations/file_locations.properties.html', 
            title=mode_title, update_type=mode, file_location=file_location, brands=brand_list)

    status, msg, file_location = fl.request_to_file_location(file_location, request.form)
    if not status:
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp='Error', e_resp_msg=msg))
        return render_template('file_locations/file_locations.properties.html', 
            title=mode_title, update_type=mode, file_location=file_location, brands=brand_list)

    status, msg = fl.save_file_location(mode, file_location, g.user)
    if status:
        flash(msg, "message")
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp='OK', e_resp_msg=msg))
        return redirect('/admin/file_locations')
    else:
        flash(msg, "error")
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp='Error', e_resp_msg=msg))
        return render_template('file_locations/file_locations.properties.html', 
            title=mode_title, update_type=mode, file_location=file_location, brands=brand_list)