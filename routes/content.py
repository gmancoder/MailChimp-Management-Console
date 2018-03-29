from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint, Response
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from sqlalchemy import *
from models.shared import login_manager
from models.users import *
from models.log import *
from models.templates import *
from models.folders import *
from models.emails import *
import functions.core as f
import functions.ajax as ajax
import functions.db as dbf
import functions.log as logf
import functions.forms as forms
import functions.templates as tmpl
import functions.system as systm
import functions.lists as lst
import functions.emails as em
import md5
import urllib2
import re
import json
from functools import wraps

content = Blueprint("content", __name__)

DEFAULT_LIST_LENGTH = 25

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@content.before_request
def before_request():
    f.Init()
    try:
        g.folders = Folder.query.filter(and_(Folder.brand_id == g.current_brand.id, Folder.folder_type.in_(['emails', 'portfolio_items', 'templates', 'template_categories']), Folder.parent_folder_id == None)).order_by(Folder.name.asc()).all()
        #g.folders = Folder.query.all()
    except Exception as ex:
        print str(ex)
    return f.CheckPermission()

def _render_properties_form(f, form_type, title, update_type, additional_objects={}):
    #print additional_objects
    form, required_fields = forms.draw_form(form_type, f, update_type, additional_objects['categories'])
    req_fields = '"%s"' % ('","'.join(required_fields))
    return render_template('%s/%s.properties.html' % (form_type, form_type), title=title, form=form, required=req_fields, update_type=update_type, objects=additional_objects)

@content.route('/template_categories')
@content.route('/template_categories/<int:page>')
def template_categories(page=1):
    query = TemplateCategory.query.filter(TemplateCategory.folder_id == g.current_folder.id)
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
        template_categories = query.paginate(page,r,False).items
    else:
        pages = 0
        template_categories = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(template_categories)))
    return render_template('template_categories/template_categories.default.html', title="Templates", template_categories=template_categories, pages=pages, current_page=page)

@content.route('/template_categories/new', methods=['GET', 'POST'])
@login_required
def new_template_category():
    if request.method == "GET":
        return _render_properties_form({}, "template_categories", "New Template Category", "new")
    else:
        if 'template_categories_name' not in request.form:
            msg = 'Missing Field "Name"'
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_properties_form(request.form, "template_categories", "New Template Category", "new")
        if tmpl.template_category_exists(g.current_brand.id, request.form['template_categories_name']):
            msg = 'Category with name "%s" already exists' % request.form['template_categories_name']
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_properties_form(request.form, "template_categories", "New Template Category", "new")
        
        status, response = tmpl.add_template_category(g.current_brand.id, request.form['template_categories_name'], g.current_folder.id, g.user.id)
        if not status:
            msg = response
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_properties_form(request.form, "template_categories", "New Template Category", "new")
        flash('Template Category added', 'info')
        return redirect('/template_categories')  

@content.route('/template_categories/<int:template_category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template_category(template_category_id):
    template_category = TemplateCategory.query.filter(and_(TemplateCategory.brand_id == g.current_brand.id, TemplateCategory.id == template_category_id)).first()
    if not template_category:
        msg = 'Template Category not found'
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
        return redirect('/template_categories')

    if request.method == "GET":
        return _render_properties_form({'template_categories_name': template_category.name}, "template_categories", template_category.name, "update")
    else:
        if 'template_categories_name' not in request.form:
            msg = 'Missing Field "Name"'
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return _render_properties_form(request.form, "template_categories", template_category.name, "update")
        if request.form['template_categories_name'] != template_category.name:
            if tmpl.template_category_exists(g.current_brand.id, request.form['template_categories_name']):
                msg = 'Category with name "%s" already exists' % request.form['template_categories_name']
                logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
                flash(msg, 'error')
                return _render_properties_form(request.form, "template_categories", template_category.name, "update")
            
            status, response = tmpl.update_template_category(template_category, request.form['template_categories_name'], g.user.id)
            if not status:
                msg = response
                logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
                flash(msg, 'error')
                return _render_properties_form(request.form, "template_categories", template_category.name, "update")
            flash('Template Category updated', 'info')
        return redirect('/template_categories')  


@content.route('/templates')
@content.route('/templates/<int:page>')
@login_required
def templates(page=1):
    query = Template.query.filter(Template.folder_id == g.current_folder.id)
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
        templates = query.paginate(page,r,False).items
    else:
        pages = 0
        templates = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(templates)))
    return render_template('templates/templates.default.html', title="Templates", templates=templates, pages=pages, current_page=page)

@content.route('/ace-test')
def ace():
    return render_template('ace_test.html', title="Ace Test")

@content.route('/templates/new', methods=['GET', 'POST'])
@content.route('/templates/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def template_details(id=None):
    template = Template()
    template.active = True
    template.html = "<p></p>"
    template.thumbnail = "";
    #template_request = {}
    mode = "new"
    mode_title = "New Template"
    log_op = 'Create'
    #objects = {'id': 0, 'html': '', 'categories': {'templates_category_id': tmpl.get_all_dict(g.current_brand.id)}}
    system_merge_fields = systm.get_all_system_merge_fields()
    list_merge_fields = lst.get_merge_fields_for_content(g.current_brand.id)
    if id != None:
        template = Template.query.filter(and_(Template.brand_id == g.current_brand.id, Template.id == id)).first()
        if not template:
            msg = 'Template not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/templates')
        #template_request = tmpl.template_to_request(template)
        mode = "update"
        mode_title = template.name
        log_op = 'Update'
        #objects = {'id': id, 'html': template.html.replace('<', '&lt;').replace('>', '&gt;'), 'categories': {'templates_category_id': tmpl.get_all_dict(g.current_brand.id)}}
    editor_html = template.html.replace('<', '&lt;').replace('>', '&gt;')
    brand_categories = tmpl.get_all(g.current_brand.id)
    if request.method == 'GET':
        return render_template('templates/templates.properties.html', title=mode_title, update_type=mode, template=template, categories=brand_categories, html=editor_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields)
    else:
        name = ""
        category_id = None
        active = False

        if 'templates_name' not in request.form:
            msg = 'Missing Field "Name"'
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('templates/templates.properties.html', title=mode_title, update_type=mode, template=template, categories=brand_categories, html=editor_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields)
        template.name = request.form['templates_name']
        if 'templates_category_id' not in request.form:
            msg = 'Missing Field "Category"'
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('templates/templates.properties.html', title=mode_title, update_type=mode, template=template, categories=brand_categories, html=editor_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields)
        template.category_id = int(request.form['templates_category_id'])
        template.active = request.form['templates_active']

        if mode == 'new':
            status, results = tmpl.template_to_mailchimp(g.current_brand.id, g.current_folder.id, template.name, template.category_id, template.active)
        else:
            status, results = tmpl.template_to_mailchimp(g.current_brand.id, g.current_folder.id, template.name, template.category_id, template.active, html=template.html, mailchimp_id=template.mailchimp_id)

        if not status:
            msg = 'Mailchimp %s FAILED - %s' % (log_op, results)
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('templates/templates.properties.html', title=mode_title, update_type=mode, template=template, categories=brand_categories, html=editor_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields)

        mc_results = json.loads(results)
        mailchimp_id = mc_results['id']
        type = mc_results['type']
        thumbnail = mc_results['thumbnail']
        status, sections = tmpl.get_template_sections(g.current_brand.id, mailchimp_id)
        if not status:
            msg = 'Error getting Template Sections - %s' % sections
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('templates/templates.properties.html', title=mode_title, update_type=mode, template=template, categories=brand_categories, html=editor_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields)

        sections = json.loads(sections)
        if mode == 'new':
            status, results = tmpl.template_to_db(g.current_brand.id, template.category_id, g.current_folder.id, mailchimp_id, template.name, type, template.active, thumbnail, g.user, sections=sections['sections'])
        else:
            status, results = tmpl.template_to_db(g.current_brand.id, template.category_id, g.current_folder.id, mailchimp_id, template.name, type, template.active, thumbnail, g.user, html=template.html, sections=sections['sections'], id=id)

        if not status:
            msg = 'DB %s FAILED - %s' % (log_op, results)
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
            return render_template('templates/templates.properties.html', title=mode_title, update_type=mode, template=template, categories=brand_categories, html=editor_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields)
        
        if mode == 'new':
            return redirect('/templates/%s/detail' % results[0]['id'])
        else:
            return redirect('/templates/%s/detail' % id)

@content.route('/emails')
@content.route('/emails/<int:page>')
@login_required
def emails(page=1):
    query = Email.query.filter(Email.folder_id == g.current_folder.id)
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
        emails = query.paginate(page,r,False).items
    else:
        pages = 0
        emails = query.all()

    logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(emails)))
    return render_template('emails/emails.default.html', title="All Email", emails=emails, pages=pages, current_page=page)

@content.route('/emails/new', methods=['GET', 'POST'])
@content.route('/emails/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def email_details(id=None):
    email = Email()
    email.full_html = "<p></p>"
    email_form = {}
    template_sections = []
    email_sections = {}
    mode = "new"
    mode_title = "New Email"
    log_op = 'Create'
    templates = tmpl.all_templates_id_dict(g.current_brand.id)
    system_merge_fields = systm.get_all_system_merge_fields()
    list_merge_fields = lst.get_merge_fields_for_content(g.current_brand.id)
    additional_objects = {'emails_template_id': templates}
    if id != None:
        email = Email.query.filter(and_(Email.brand_id == g.current_brand.id, Email.id == id)).first()
        if not email:
            msg = 'Email not found'
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
            return redirect('/emails')
        mode = "update"
        mode_title = email.name
        log_op = 'Update'
        template_sections = tmpl.template_sections(g.current_brand.id, email.template_id)
        email_sections = em.email_sections_dict(email)

    editor_html = email.full_html.replace('<', '&lt;').replace('>', '&gt;')
    preview_html = email.full_html
    id = email.id

    email_dict = em.email_to_form_dict(email)
    if request.method == 'POST':
        email_dict = request.form
    form, required_fields = forms.draw_form("emails", email_dict, mode, additional_objects)
    
    if request.method == 'GET':
        return render_template('emails/emails.properties.html', title=mode_title, update_type=mode, form=form, required_fields=required_fields, html=editor_html, preview_html=preview_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields, id=id, template_sections=template_sections, email_sections=email_sections)

    # POST
    for field in required_fields:
        if field not in request.form:
            msg = '%s required' % field.replace('emails_', '')
            flash(msg, 'error')
            logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
            return render_template('emails/emails.properties.html', title=mode_title, update_type=mode, form=form, required_fields=required_fields, html=editor_html, preview_html=preview_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields, id=id, template_sections=template_sections, email_sections=email_sections)

    name = request.form['emails_name']
    template_id = request.form['emails_template_id']
    subject = request.form['emails_subject']
    status, response = em.email_to_db(g.current_brand.id, template_id, name, subject, g.current_folder.id, g.user, id=id)
    if not status:
        msg = 'Saving Email FAILED - ' % response
        flash(msg, 'error')
        logf.AddLog(Log(g.current_brand.id, g.current_tool.id, g.user.id, request.path, op=log_op, e_resp="Error", e_resp_msg=msg))
        return render_template('emails/emails.properties.html', title=mode_title, update_type=mode, form=form, required_fields=required_fields, html=editor_html, preview_html=preview_html, system_merge_fields=system_merge_fields, list_merge_fields=list_merge_fields, id=id, template_sections=template_sections, email_sections=email_sections)
    print response
    return redirect('/emails/%s/detail' % response)