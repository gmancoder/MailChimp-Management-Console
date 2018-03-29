#!/usr/bin/env python
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from models.shared import login_manager
from models.tools import *
from models.users import *
from models.brands import *
from models.log import *
import functions.core as f
import functions.log as logf
import md5
import datetime

users = Blueprint("users", __name__)
DEFAULT_LIST_LENGTH = 25

@users.before_request
def before_request():
    f.Init()
    #return f.CheckPermission()

@users.route('/admin/manage_users', methods =['GET'])
@login_required
def users_home_route():
    return redirect('/admin/users')

@users.route('/admin/users', methods =['GET'])
@users.route('/admin/users/<int:page>', methods =['GET'])
@login_required
def users_home(page=1):
    all_users = User.query
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
        pages = all_users.count() / r;
        if q:
            all_users = all_users.filter(or_(User.name.like('%%%s%%' % q), User.email.like('%%%s%%' % q), User.username.like('%%%s%%' % q))).order_by(User.name).paginate(page, r, False).items
        else:
            all_users = all_users.order_by(User.name).paginate(page,r,False).items
    else:
        pages = 0
        if q:
            all_users = all_users.filter(or_(User.name.like('%%%s%%' % q), User.email.like('%%%s%%' % q), User.username.like('%%%s%%' % q))).order_by(User.name).all()
        else:
            all_users = all_users.order_by(User.name).all()
    #all_users = User.query.order_by(User.username.asc()).all()
    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Retrieve', rows=len(all_users)))
    return render_template("admin/users/admin.users.html", title='Manage Users', show_help=0, users=all_users, pages=pages, current_page=page, rows=r, q=q)

@users.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    all_brands = Brand.query.filter(Brand.status == 1).order_by(Brand.client.asc()).all()
    msg = ""
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).count() > 0:
            msg = 'User with email %s already exists' % request.form['email']
            flash(msg, "error")
        elif User.query.filter_by(username=request.form['username']).count() > 0:
            msg = 'User with username %s already exists' % request.form['username']
            flash(msg, "error")
        else:
            user = User()
            user.name = request.form['name']
            user.email = request.form['email']
            user.username = request.form['username']
            user.password = md5.new(request.form['password']).hexdigest()
            #print request.form
            if 'status' in request.form:
                user.status = 1
            else:
                user.status = 0
            user.created_by = g.user.username
            user.updated_by = g.user.username

            for brand in request.form.getlist('user_brand'):
                user.brands.append(Brand.query.get(brand))

            db.session.add(user)
            db.session.commit()
            msg = "User %s added" % user.username
            flash (msg, "message")
            logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="OK", e_resp_msg=msg))
            return redirect(url_for("users.users_home"))
    if msg != "":
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp="Error", e_resp_msg=msg))
    return render_template("admin/users/admin.users.new.html", brands=all_brands, title='New User', show_help=0)

@users.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def show_edit_user(user_id):
    user = User.query.get(user_id)
    user_tool_ids = []
    user_brand_ids = []
    for b in user.brands.all():
        user_brand_ids.append(b.id)
    all_brands = Brand.query.filter(Brand.status == 1).order_by(Brand.client.asc()).all()
    if request.method == 'GET':
        return render_template('admin/users/admin.users.edit.html', brands=all_brands, title=user.name, show_help=0, user=user, user_brands=user_brand_ids)

    user.name = request.form['name']
    user.email = request.form['email']
    user.username = request.form['username']
    if 'password' in request.form and request.form['password'] != '':
        user.password = md5.new(request.form['password']).hexdigest()
    if 'status' in request.form:
        user.status = 1
    else:
        user.status = 0
    user.updated = datetime.datetime.now()
    user.updated_by = g.user.username

    for brand in user.brands:
        user.brands.remove(brand)

    db.session.flush()
    db.session.commit()

    for brand in request.form.getlist('user_brand'):
        new_brand = Brand.query.get(brand)
        if new_brand not in user.brands:
            user.brands.append(new_brand)

    db.session.commit()
    msg = "User %s updated" % user.username
    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="OK", e_resp_msg=msg))
    flash (msg, "message")
    return redirect(url_for("users.users_home"))

@users.route('/admin/users/<int:user_id>/togglestatus', methods=['GET'])
@login_required
def toggle_status(user_id):
    user_item = User.query.get(user_id)
    if user_item != None:
        user_item.status = abs(user_item.status - 1)
        db.session.commit()
        msg = 'User %s updated' % (user_item.name)
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="OK", e_resp_msg=msg))
        flash(msg, "message")
    else:
        msg = 'User with ID %s doesn\'t exist' % user_id
        flash(msg, "error")
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Update', e_resp="Error", e_resp_msg=msg))
    return redirect(url_for("users.users_home"))

@users.route('/admin/users/<int:user_id>/delete', methods=['GET'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user != None:
        db.session.delete(user)
        db.session.commit()
        msg = "User deleted"
        flash(msg, "message")
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp="OK", e_resp_msg=msg))
    else:
        msg = 'User with ID %s doesn\'t exist' % user_id
        flash(msg, "error")
        logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp="Error", e_resp_msg=msg))
    return redirect(url_for("users.users_home"))
