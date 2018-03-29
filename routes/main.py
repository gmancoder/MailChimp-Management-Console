#!/usr/bin/env python

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint, Response
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from models.shared import login_manager
from models.users import *
from models.log import *
from models.folders import *
import functions.core as f
import functions.ajax as ajax
import functions.db as dbf
import functions.log as logf
import functions.tools as tools
import md5
import urllib2
import re
from functools import wraps

main = Blueprint("main", __name__)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@main.before_request
def before_request():
    f.Init()
    session['current_folder'] = None

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    if _check_login(username, password):
        flash('Logged in successfully', 'info')
        return redirect(request.args.get('next') or url_for('main.index'))
    else:
        flash('Username or Password is invalid' , 'danger')
        return redirect(url_for('main.login'))

def _check_login(username, password):
    hash_passwd = md5.new(password).hexdigest()
    registered_user = User.query.filter_by(username=username,password=hash_passwd).first()
    if registered_user is None:
        return False
    login_user(registered_user)
    return True

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not _check_login(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route("/profile/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'GET':
        return render_template('profile.change_password.html', title='Change Password', show_help=0)
    user = User.query.get(g.user.id)
    user.password = md5.new(request.form['password']).hexdigest()
    db.session.commit()
    flash('Password changed', 'info')
    return redirect(url_for("main.index"))

@main.route("/")
@login_required
def index():
    return render_template("index.html", title='Dashboards', show_help=0)


@main.route('/home/<int:mid>')
@login_required
def mid_change(mid):
    session['current_brand'] = mid
    return redirect(url_for("main.index"))

@main.route('/folder/<int:folder_id>')
@login_required
def folder(folder_id):
    folder = Folder.query.get(folder_id)
    url = "/"
    if folder:
        session['current_folder'] = folder_id
        tool = tools.tool_by_alias(folder.folder_type)
        if tool and tool.is_admin:
            url = '%sadmin/' % url
        url = '%s%s' % (url, folder.folder_type)
    return redirect(url)

@main.route("/api/<string:action>/<string:method>", methods=['GET', 'POST'])
@main.route("/api/<string:action>/<string:method>.<string:return_type>", methods=['GET', 'POST'])
@requires_auth
def ajax_helper(action, method, return_type = 'json'):
    global request
    return_message = ""
    if return_type.upper() in ("XML", "JSON"): 
        return f.HandleAJAXRequest(action, method, return_type)
    else:
        return_message = "Request invalid"
        request = {"action": action, "method": method, "response_type": return_type}
    return f.HandleAJAXResponse("Error",request, [{'Error': return_message}], return_type, "Error")

@main.route('/img_proxy', methods=['GET', 'POST'])
@login_required
def image_proxy():
    url = request.args.get('url')
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    return Response(response.read(), mimetype="image/jpeg")