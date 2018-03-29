#!/usr/bin/env python
import re
import unidecode
from models.shared import db
from models.users import *
from models.tools import *
from models.brands import *
from models.folders import *
import datetime
from flask import redirect, url_for, g, request, flash, session
from flask_login import current_user, AnonymousUserMixin
import functions.ajax as ajax
import functions.db as dbf
import functions.folders as folders
import xml.sax.saxutils as sax
import json
from sqlalchemy import *
import pycountry
import base64
import urllib
import urllib2
import os
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

UNCHECKED_ROUTES = ['/', '/logout', '/ajax/helper/xml', '/ajax/helper/json', '/ajax/helper', '/export', '/img_proxy']

def GetRoot():
    path = os.path.dirname(os.path.abspath(__file__))
    path = path.replace('/functions', '')
    if not path.endswith('/'):
        path = '%s/' % path
    return path

def Init():
    g.user = current_user._get_current_object()
    if g.user.is_authenticated:
        try:
            CheckForStaleSessions()
            all_tool_groups = ToolGroup.query.filter(ToolGroup.status == 1).order_by(ToolGroup.rank.asc(), ToolGroup.name.asc()).all()
            all_brands = Brand.query.filter(Brand.status == 1).order_by(Brand.client.asc()).all()
            g.tool_groups = all_tool_groups
            g.user_brands = GetCurrentUserBrands(g.user, all_brands)
            g.user_session = CheckUserSession(g.user.id)
            g.current_tool = GetCurrentTool()
            g.current_brand = GetCurrentBrand()
            g.brand_tools = GetCurrentBrandTools()
            if g.user.is_admin():
                g.admin_tools = Tool.query.filter(Tool.group_id==1).order_by(Tool.rank.asc()).all()
            if 'current_folder' in session and session['current_folder'] != None:
                g.current_folder = Folder.query.get(session['current_folder'])
                if g.current_tool != None and g.current_folder.folder_type != g.current_tool.alias:
                    g.current_folder = folders.get_root_folder(g.current_brand.id, g.current_tool.alias)
                    if g.current_folder == None:
                        g.current_folder = folders.create_root_folder(g.current_brand.id, g.current_tool.alias)
                    session['current_folder'] = g.current_folder.id
            elif g.current_brand and g.current_tool:
                g.current_folder = Folder.query.filter(and_(Folder.brand_id == g.current_brand.id, Folder.folder_type == g.current_tool.alias)).first()
                if g.current_folder == None:
                    g.current_folder = folders.create_root_folder(g.current_brand.id, g.current_tool.alias)
                session['current_folder'] = g.current_folder.id
            else:
                print 'Current Brand: %s' % g.current_brand
                print 'Current Tool: %s' % g.current_tool
        except Exception as ex:
            print ex.args
            print type(ex)
            traceback.print_exc()

def GetCurrentTool():
    if request.path.startswith('/ajax/helper'):
        if request.form and 'tool' in request.form:
            return Tool.query.filter(Tool.alias == request.form['tool']).first()

    all_tools = Tool.query.all()
    for tool in all_tools:
        if request.path.startswith(tool.home_route) or request.path.startswith('/%s' % tool.alias):
            return tool

    return None

def GetCurrentUserBrands(current_user, all_brands):
    brands_to_display = []
    if current_user.is_authenticated:
        for brand in all_brands:
            if brand in current_user.brands and brand.status == 1:
                brands_to_display.append(brand)
    return brands_to_display

def GetCurrentBrand():
    brand = None
    if 'current_brand' in session:
        current_brand = session['current_brand']
        brand = Brand.query.filter(Brand.mid == current_brand).first()
    else:
        if len(g.user_brands) > 0:
            brand = g.user_brands[0]
            session['current_brand'] = brand.mid
    return brand

def GetCurrentBrandTools():
    groups_to_display = {}
    if g.user.is_authenticated and g.current_brand != None:
        for group in g.tool_groups:
            for tool in group.tools:
                if tool in g.current_brand.tools and tool.status == 1:
                    if group.name not in groups_to_display:
                        groups_to_display[group.name] = []
                    groups_to_display[group.name].append(tool)
    return groups_to_display

def CheckPermission():
    check_ok = False
    if g.user.is_authenticated:
        if request.path not in UNCHECKED_ROUTES:
            if g.current_tool.is_admin == 1 and g.user.admin:
                check_ok = True
            for tool in g.current_brand.tools:
                if tool.alias == g.current_tool.alias:
                    check_ok = True

            if not check_ok:
                flash('Access Denied', 'error')
                return redirect(url_for("main.index"))
    return None

def CheckForStaleSessions():
    stale_def = datetime.datetime.now() - datetime.timedelta(hours=8)
    stale_sessions = UserSession.query.filter(UserSession.last_used < stale_def).all()
    for sess in stale_sessions:
        db.session.delete(sess)

def GetUserSession(user_id):
    return UserSession.query.filter_by(user_id=user_id).first()

def CheckUserSession(user_id):
    sess = GetUserSession(user_id)
    if sess == None:
        sess = UserSession(user=user_id)
        sess.last_used = datetime.datetime.now()
        db.session.add(sess)
        db.session.commit()
    else:
        sess.last_used = datetime.datetime.now()
        db.session.commit()
    return sess
def GetToolSettingValue(tool_alias, setting_key):
    setting = ToolSetting.query.filter(ToolSetting.tool.has(Tool.alias==tool_alias), ToolSetting.key == setting_key).first()
    if setting != None:
        return setting.value
    return None

def GetBrandByID(brand_id):
    return Brand.query.get(brand_id)

def GenerateAlias(s):
    clean_str = re.sub(r'[^0-9A-Za-z]', '_', s)
    return clean_str.lower()
def GeneratePassword(mid, user):
    user_1 = user.split('_')[0]
    return '%s_%s!' % (user_1, mid[-4:])

def GetDateRange(date_ymd, days):
    time = datetime.datetime.strptime(date_ymd, "%Y%m%d")
    time_end = time + datetime.timedelta(days=7)
    dates = []
    while time <= time_end:
        dates.append(time.strftime("%Y%m%d"))
        time = time + datetime.timedelta(days=1)

    return time, time_end, dates

def HandleAJAXRequest(action, method, response_type):
    status, status_msg, request, results = ajax.Request(action, method, response_type)
    result_type = "Result"
    if not status:
        result_type = "Error"
    return HandleAJAXResponse(status_msg, request, results, response_type, result_type)

def HandleAJAXResponse(msg, request, results, type, result_type):
    if type.upper() == "JSON":
        response = {"Status": msg, "Request": request, "%ss" % result_type: results}
        return json.dumps(response)
    else:
        xml = """<?xml version="1.0" ?><Response>
        <Status>%s</Status>
        <Request>
        <Action>%s</Action>
        <Method>%s</Method>
        <Response_Type>%s</Response_Type>
        </Request>
        <%ss>""" % (msg, request['action'], request['method'], request['response_type'], result_type)
        for result in results:
            xml += "<%s>" % result_type
            for key, value in result.items():
                xml += "<%s>%s</%s>" % (sax.escape(key), sax.escape(value), sax.escape(key))
            xml += "</%s>" % result_type
        xml += """</%ss>
        </Response>""" % result_type
        return xml

def GetDateRange(date_ymd, days):
    time = datetime.datetime.strptime(date_ymd, "%Y%m%d")
    time_end = time + datetime.timedelta(days=7)
    dates = []
    while time <= time_end:
        dates.append(time.strftime("%Y%m%d"))
        time = time + datetime.timedelta(days=1)

    return time, time_end, dates

def FieldNamesFromDict(field_dict_list):
    field_names = []
    for field in field_dict_list:
        field_names.append(unidecode.unidecode(field['Name']))
    return field_names

def SortDataDict(data, fields):
    for field in fields:
        data = sorted(data, key=lambda k: k[field])
    return data

def ImageProxy(content):
    matches = re.findall('src="([^"]+)"',content)
    prefix = "/img_proxy?url="
    print matches
    for match in matches:
        repl = prefix + match
        print repl
        content = content.replace(match,repl)

    return content
def PostRemoteData(url, data=None, auth=None, method=None, additional_headers=[]):
    if data != None:
        if isinstance(data, dict):
            post_data_encoded = urllib.urlencode(data)
        else:
            post_data_encoded = data
        #make a request object to hold the POST data and the URL
        request_object = urllib2.Request(url, post_data_encoded)
    else:
        request_object = urllib2.Request(url)
    #make the request using the request object as an argument, store response in a variable
    if auth != None:
        request_object.add_header("Authorization", "apikey %s" % auth)
    if method != None:
        request_object.get_method = lambda: method
    for header in additional_headers:
        request_object.add_header(header['Name'], header['Value'])
    response = urllib2.urlopen(request_object)
    #store request response in a string
    html_string = response.read()
    return html_string

def SendEmail(from_email, from_alias, to, subject, content, body_type='plain', attachments=[]):
    #print 'Email Currently Offline'
    #print content
    me = from_email
    you = to

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_alias
    msg['To'] = to

    body = MIMEText(content, body_type)
    msg.attach(body)

    for f in attachments or []:
        with open(f, "rb") as fil:
            msg.attach(MIMEApplication(
                fil.read(),
                Content_Disposition='attachment; filename="%s"' % os.path.basename(f),
                Name=os.path.basename(f)
            ))

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    try:
        s = smtplib.SMTP('webserver25.turnkeywebspace.com')
        s.login("mmc@hometowncomputerny.com", "!MailChimp#16")
    except:
        s = smtplib.SMTP()
        s.connect("smtp.googlemail.com",587)
        s.starttls()
        s.login("grbrewer@gmail.com", "!gbrewer#10")
        #print 'Using google mail'
    s.sendmail(me, [you], msg.as_string())
    s.quit()


def setup_mailchimp_connect(brand):
    url = 'https://%s.api.mailchimp.com/3.0/' % brand.api_dc
    
    auth = base64.encodestring('%s:%s' % (brand.api_user, brand.api_key)).replace("\n", "")
    return url, auth

def post_to_mailchimp(brand, data_type, data_str=None, method="POST", include_header=True):
    json_header = [{'Name': 'Content-Type', 'Value': 'application/json'}]
    url, auth = setup_mailchimp_connect(brand)
    url = '%s%s' % (url, data_type)
    print url
    print data_str
    try:
        if include_header:
            resp = PostRemoteData(url, data=data_str, method=method, auth=brand.api_key, additional_headers=json_header)
        else:
            resp = PostRemoteData(url, data=data_str, method=method, auth=brand.api_key)
        return True, resp
    except Exception as e:
        return False, str(e)

def patch_to_mailchimp(brand, data_type, data_str, id, method="PATCH"):
    json_header = [{'Name': 'Content-Type', 'Value': 'application/json'}]
    url, auth = setup_mailchimp_connect(brand)
    url = '%s%s/%s' % (url, data_type, id)
    print url
    print data_str
    try:
        resp = PostRemoteData(url, data=data_str, auth=brand.api_key, method=method, additional_headers=json_header)
        return True, resp
    except Exception as e:
        return False, str(e)

def patch_to_mailchimp_2(brand, data_type, data_str):
    json_header = [{'Name': 'Content-Type', 'Value': 'application/json'}]
    url, auth = setup_mailchimp_connect(brand)
    url = '%s%s' % (url.replace('3.0', '2.0'), data_type)
    print url
    print data_str
    try:
        resp = PostRemoteData(url, data=data_str, additional_headers=json_header)
        return True, resp
    except Exception as e:
        return False, str(e)

def delete_to_mailchimp(brand, data_type, id):
    json_header = [{'Name': 'Content-Type', 'Value': 'application/json'}]
    url, auth = setup_mailchimp_connect(brand)
    url = '%s%s/%s' % (url, data_type, id)
    print url
    try:
        resp = PostRemoteData(url, auth=brand.api_key, method="DELETE", additional_headers=json_header)
        return True, resp
    except Exception as e:
        return False, str(e)

def _obj_to_dict(objects):
    r_objects = []
    for obj in objects:
        try:
            r_object = obj.__dict__
        except Exception as ex:
            r_object = vars(obj)
        for k,v in r_object.items():
            r_object[k] = str(v)
            #if isinstance(v, datetime.datetime):
            #    r_object[k] = str(v)
        
        #del r_object['_sa_instance_state']
        #if 'created' in r_object:
        #    r_object['created'] = str(r_object['created'])
        #if 'updated' in r_object:
        #    r_object['updated'] = str(r_object['updated'])
        r_objects.append(r_object)
    #print r_objects
    return r_objects

def camel(string):
    string = string.replace('_', ' ')
    string = string.title()
    if string == 'Id':
        string = "ID"
    else:
        string = string.replace(' ', '')
    return string