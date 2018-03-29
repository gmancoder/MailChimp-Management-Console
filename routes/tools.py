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
import md5
import datetime
import inflection

tools = Blueprint("tools", __name__)
DEFAULT_LIST_LENGTH = 25

@tools.before_request
def before_request():
    f.Init()
    #return f.CheckPermission()

@tools.route('/admin/tools', methods =['GET'])
@tools.route('/admin/tools/<int:page>', methods =['GET'])
@login_required
def tools_home(page=1):
    tools = Tool.query
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
        pages = tools.count() / r;
        if q:
            tools = tools.filter(Tool.name.like('%%%s%%' % q)).order_by(Tool.name).paginate(page, r, False).items
        else:
            tools = tools.order_by(Tool.name).paginate(page,r,False).items
    else:
        pages = 0
        if q:
            tools = tools.filter(Tool.name.like('%%%s%%' % q)).order_by(Tool.name).all()
        else:
            tools = tools.order_by(Tool.name).all()
    #tool_groups = ToolGroup.query.order_by(ToolGroup.name).all()
    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(tools)))
    return render_template("admin/tools/admin.tools.html", tools=tools, title='Manage Tools', show_help=0, pages=pages, current_page=page, rows=r, q=q)

@tools.route('/admin/tools/groups/new', methods =['GET', 'POST'])
@login_required
def tool_group_new():
    if request.method == 'POST':
        if len(ToolGroup.query.filter_by(name=request.form['name']).all()) == 0:
            new_tool_group = ToolGroup()
            new_tool_group.name = request.form['name']
            new_tool_group.rank = request.form['rank']
            new_tool_group.icon = request.form['icon']
            if request.form['alias'] != '':
                new_tool_group.alias = request.form['alias']
            else:
                new_tool_group.alias = f.GenerateAlias(new_tool_group.name)
            new_tool_group.created_by = g.user.username
            new_tool_group.updated_by = g.user.username
            db.session.add(new_tool_group)
            db.session.commit()
            msg = 'Tool Group %s has been created' % new_tool_group.name
            logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="OK", e_resp_msg=msg))
            flash(msg, 'message')
            return redirect(url_for("tools.tools_home"))
        else:
            logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            msg = 'Tool Group with name %s already exists' % request.form['name']
            flash(msg, 'error')
    return render_template("admin/tools/admin.tools.groups.new.html", title='Create Tool Group', show_help=0)

@tools.route('/admin/tools/groups/<int:tool_group_id>/edit', methods=['GET', 'POST'])
@login_required
def show_edit_tool_group(tool_group_id):
    tool_group_item = ToolGroup.query.get(tool_group_id)
    if request.method == 'GET':
        return render_template('admin/tools/admin.tools.groups.edit.html', title=tool_group_item.name, show_help=0, group=tool_group_item)

    tool_group_item.name = request.form['name']
    tool_group_item.rank = request.form['rank']
    tool_group_item.icon = request.form['icon']
    if request.form['alias'] != '':
        tool_group_item.alias = request.form['alias']
    else:
        tool_group_item.alias = f.GenerateAlias(tool_group_item.name)
    tool_group_item.updated_by = g.user.username
    tool_group_item.updated = datetime.datetime.now()
    db.session.commit()
    msg="Tool Group %s updated" % tool_group_item.name
    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="OK", e_resp_msg=msg))
    flash(msg, "message")
    return redirect(url_for("tools.tools_home"))

@tools.route('/admin/tools/groups/<int:tool_group_id>/togglestatus', methods=['GET'])
@login_required
def toggle_status_group(tool_group_id):
    tool_group_item = ToolGroup.query.get(tool_group_id)
    if tool_group_item != None:
        tool_group_item.status = abs(tool_group_item.status - 1)
        db.session.commit()
        msg = 'Tool Group %s updated' % (tool_group_item.name)
        flash(msg, "message")
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="OK", e_resp_msg=msg))
    else:
        msg = 'Tool Group with ID %s doesn\'t exist' % tool_group_id
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
        flash(msg, "error")
    return redirect(url_for("tools.tools_home"))

@tools.route('/admin/tools/groups/<int:tool_group_id>/delete', methods=['GET'])
@login_required
def delete_tool_group(tool_group_id):
    tool_group_item = ToolGroup.query.get(tool_group_id)
    if tool_group_item.tools.count() > 0:
        msg="Tool group %s cannot be deleted because it contains tools" % tool_group_item.name
        flash(msg, "error")
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp="Error", e_resp_msg=msg))
    else:
        db.session.delete(tool_group_item)
        db.session.commit()
        msg='Tool group %s deleted' % tool_group_item.name
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp="OK", e_resp_msg=msg))
        flash(msg, "message")
    return redirect(url_for("tools.tools_home"))

@tools.route('/admin/tools/new', methods =['GET', 'POST'])
@login_required
def tools_new():
    tool_groups = ToolGroup.query.order_by(ToolGroup.name).all()
    if request.method == 'POST':
        if Tool.query.filter(Tool.name==request.form['name']).count() == 0:
            print request.form
            new_tool = Tool()
            new_tool.name = request.form['name']
            new_tool.description = request.form['description']
            new_tool.rank = request.form['rank']
            new_tool.group_id = request.form['group_id']
            new_tool.home_route = request.form['home_route']
            if 'is_admin' in request.form:
                new_tool.is_admin = 1
            else:
                new_tool.is_admin = 0
            if request.form['alias'] != '':
                new_tool.alias = request.form['alias']
            else:
                new_tool.alias = f.GenerateAlias(new_tool.name)
            new_tool.created_by = g.user.username
            new_tool.updated_by = g.user.username

            template_path = '%stemplates/%s/' % (f.GetRoot(), new_tool.alias)
            tmpl_path = '%stemplates/_TMPL/' % f.GetRoot()
            static_css_path = '%sstatic/css/' % f.GetRoot()
            static_js_path = '%sstatic/js/' % f.GetRoot()
            tool_group = tls.tool_group_by_id(int(new_tool.group_id))
            if not tool_group:
                msg = "Tool Group with ID %s not found" % new_tool.group_id
                logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="OK", e_resp_msg=msg))
                flash(msg, 'error')
            else:
                route_path = '%sroutes/%s.py' % (f.GetRoot(), tool_group.alias)
                route_tmpl_path = '%sroutes/tmpl.txt' % f.GetRoot()
                if not os.path.exists(template_path) and os.path.exists(route_path):
                    os.mkdir(template_path)
                    tls.touch_file('%stools.%s.css' % (static_css_path, new_tool.alias))
                    tls.touch_file('%stools.%s.js' % (static_js_path, new_tool.alias))

                    files = ['default', 'properties']
                    for part in files:
                        tls.write_template('%sTOOL_ALIAS.%s.html' % (tmpl_path, part), '%s%s.%s.html' % (template_path, new_tool.alias, part), new_tool.name, new_tool.alias)

                    tls.write_template(route_tmpl_path, route_path, new_tool.name, new_tool.alias, True)

                    db.session.add(new_tool)
                    db.session.commit()

                    msg='Tool %s has been created' % new_tool.name
                    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="OK", e_resp_msg=msg))
                    flash(msg, 'message')
                    return redirect(url_for("tools.tools_home"))
                else:
                    msg = "Unable to map to route file %s" % route_path
                    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="OK", e_resp_msg=msg))
                    flash(msg, 'error')
        else:
            msg='Tool with name %s already exists' % request.form['name']
            logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            flash(msg, 'error')
    return render_template("admin/tools/admin.tools.new.html", title='Create Tool', show_help=0, groups=tool_groups)

@tools.route('/admin/tools/<int:tool_id>/edit', methods=['GET', 'POST'])
@login_required
def show_edit_tool(tool_id):
    tool_item = Tool.query.get(tool_id)
    tool_groups = ToolGroup.query.order_by(ToolGroup.name).all()
    if request.method == 'GET':
        return render_template('admin/tools/admin.tools.edit.html', title=tool_item.name, show_help=0, groups=tool_groups, tool=tool_item)

    if request.form['form'] == "tool":
        tool_item.name = request.form['name']
        tool_item.description = request.form['description']
        tool_item.rank = request.form['rank']
        tool_item.group_id = request.form['group_id']
        tool_item.home_route = request.form['home_route']
        if 'is_admin' in request.form:
            tool_item.is_admin = 1
        else:
            tool_item.is_admin = 0
        if request.form['alias'] != '':
            tool_item.alias = request.form['alias']
        else:
            tool_item.alias = f.GenerateAlias(tool_item.name)
        tool_item.updated_by = g.user.username
        tool_item.updated = datetime.datetime.now()
        db.session.commit()
        msg="Tool %s updated" % tool_item.name
        flash(msg, "message")
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="OK", e_resp_msg=msg))
        return redirect(url_for("tools.tools_home"))
    elif request.form['form'] == "setting":
        key = request.form['key']
        value = request.form['value']
        tool_id = request.form['tool_id']

        if ToolSetting.query.filter_by(key=key,tool_id=tool_id).count() == 0:
            new_setting = ToolSetting(key, value)
            new_setting.tool_id = tool_id
            new_setting.created_by = g.user.username
            new_setting.updated_by = g.user.username

            db.session.add(new_setting)
            db.session.commit()
            msg = 'Setting "%s" added' % key
            logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="OK", e_resp_msg=msg))
            flash(msg, "message")
        else:
            msg='Setting with key "%s" already exists' % key
            logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
            flash(msg, "error")

        t_id = int(tool_id)
        return redirect(url_for("tools.show_edit_tool", tool_id=t_id))

@tools.route('/admin/tools/<int:tool_id>/togglestatus', methods=['GET'])
@login_required
def toggle_status(tool_id):
    tool_item = Tool.query.get(tool_id)
    if tool_item != None:
        tool_item.status = abs(tool_item.status - 1)
        db.session.commit()
        msg='Tool %s updated' % (tool_item.name)
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="OK", e_resp_msg=msg))
        flash(msg, "message")
    else:
        msg='Tool with ID %s doesn\'t exist' % tool_id
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
        flash(msg, "error")
    return redirect(url_for("tools.tools_home"))

@tools.route('/admin/tools/<int:tool_id>/delete',methods=['GET'])
@login_required
def delete_tool(tool_id):
    tool_item = Tool.query.get(tool_id)
    if tool_item.brands.count() > 0:
        msg="Tool %s cannot be deleted because brands are associated with it" % tool_item.name
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp="Error", e_resp_msg=msg))
        flash(msg, "error")
    else:
        db.session.delete(tool_item)
        db.session.commit()
        msg = 'Tool %s deleted' % tool_item.name
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp="OK", e_resp_msg=msg))
        flash(msg, "message")
    return redirect(url_for("tools.tools_home"))

@tools.route('/admin/tools/<int:tool_id>/settings/<int:setting_id>/delete', methods=['GET'])
@login_required
def delete_setting(tool_id, setting_id):
    setting = ToolSetting.query.get(setting_id)
    db.session.delete(setting)
    db.session.commit()
    msg = 'Setting deleted'
    flash(msg)
    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp="OK", e_resp_msg=msg))
    return redirect(url_for("tools.show_edit_tool", tool_id=int(tool_id)))
