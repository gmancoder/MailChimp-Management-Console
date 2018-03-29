from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Blueprint
from flask_login import LoginManager,login_user , logout_user , current_user , login_required
from models.shared import login_manager
from models.tools import *
from models.brands import *
from models.log import *
import functions.core as f
import functions.log as logf
import md5
import datetime

brands = Blueprint("brands", __name__)
DEFAULT_LIST_LENGTH = 25

@brands.before_request
def before_request():
    f.Init()
    #return f.CheckPermission()

@brands.route('/admin/brands', methods=['GET'])
@brands.route('/admin/brands/<int:page>', methods=['GET'])
@login_required
def brand_home(page=1):
    all_brands = Brand.query
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
        pages = all_brands.count() / r;
        if q:
            all_brands = all_brands.filter(Brand.client.like('%%%s%%' % q)).order_by(Brand.client).paginate(page, r, False).items
        else:
            all_brands = all_brands.order_by(Brand.client).paginate(page,r,False).items
    else:
        pages = 0
        if q:
            all_brands = all_brands.filter(Brand.client.like('%%%s%%' % q)).order_by(Brand.client).all()
        else:
            all_brands = all_brands.order_by(Brand.client).all()
    logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Retrieve', e_resp='OK', rows=len(all_brands)))
    return render_template('admin/brands/admin.brands.html', title='All Brands', show_help=0, brands=all_brands, pages=pages, current_page=page, rows=r, q=q)

@brands.route('/admin/brands/new', methods=['GET','POST'])
@login_required
def new_brand():
    all_tools = Tool.query.filter(Tool.status == 1).order_by(Tool.name.asc()).all()
    if request.method == 'POST':
        try:
            mid = request.form['mid']
            if Brand.query.filter_by(mid=mid).count() == 0:
                new_brand = Brand()
                new_brand.mid = request.form['mid']
                new_brand.client = request.form['client_name']
                new_brand.api_user = request.form['api_user']
                new_brand.api_key = request.form['api_key']
                new_brand.api_dc = request.form['api_dc']
                if 'status' in request.form:
                    new_brand.status = 1
                else:
                    new_brand.status = 0
                new_brand.created_by = g.user.username
                new_brand.updated_by = g.user.username

                if 'brand_tool' in request.form:
                    for tool in request.form.getlist('brand_tool'):
                        new_brand.tools.append(Tool.query.get(tool))

                db.session.add(new_brand)
                db.session.commit()

                msg = "Brand %s (%s) added" % (new_brand.client, mid)
                flash(msg, "message")
                logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp='OK', e_resp_msg=msg))
                return redirect(url_for("brands.brand_home"))
            else:
                msg = "Brand with MID %s already exists" % mid
                logf.AddLog(Log(1, g.current_tool.id, g.user.id, request.path, op='Create', e_resp='Error', e_resp_msg=msg))
                flash(msg, "error")
        except Exception as e:
            flash(str(e), "error")
    return render_template("admin/brands/admin.brands.new.html", tools=all_tools, title="New Brand",show_help=0)

@brands.route('/admin/brands/<int:mid>/edit', methods=['GET', 'POST'])
@login_required
def show_edit_brand(mid):
    brand_tool_ids = []
        
    brand_item = Brand.query.filter(Brand.mid==mid).first()
    for t in brand_item.tools.all():
        brand_tool_ids.append(t.id)
    all_tools = Tool.query.filter(Tool.status == 1).order_by(Tool.name.asc()).all()
    if request.method == 'GET':
        return render_template('admin/brands/admin.brands.edit.html', brand_tools=brand_tool_ids, tools=all_tools, title='%s (%s)' % (brand_item.client, brand_item.mid), show_help=0, brand=brand_item)

    brand_item.mid = request.form['mid']
    brand_item.client = request.form['client_name']
    brand_item.api_user = request.form['api_user']
    brand_item.api_key = request.form['api_key']
    brand_item.api_dc = request.form['api_dc']
    if 'status' in request.form:
        brand_item.status = 1
    else:
        brand_item.status = 0
    brand_item.updated = datetime.datetime.now()
    brand_item.updated_by = g.user.username
    for tool in brand_item.tools:
        brand_item.tools.remove(tool)

    db.session.flush()
    db.session.commit()

    for tool in request.form.getlist('brand_tool'):
        new_tool = Tool.query.get(tool)
        if new_tool not in brand_item.tools:
            brand_item.tools.append(new_tool)

    db.session.commit()
    msg = 'Brand %s (%s) updated' % (brand_item.client, brand_item.mid)
    flash(msg, "message")
    logf.AddLog(Log(brand_item.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp='OK', e_resp_msg=msg))
    return redirect(url_for("brands.brand_home"))

@brands.route('/admin/brands/<int:brand_id>/togglestatus', methods=['GET'])
@login_required
def toggle_status(brand_id):
    brand_item = Brand.query.get(brand_id)
    if brand_item != None:
        brand_item.status = abs(brand_item.status - 1)
        db.session.commit()
        msg ='Brand %s (%s) updated' % (brand_item.client, brand_item.mid)
        logf.AddLog(Log(brand_item.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp='OK', e_resp_msg=msg))
        flash(msg, "message")
    else:
        msg = 'Brand with ID %s doesn\'t exist' % brand_id
        logf.AddLog(Log(brand_item.id, g.current_tool.id, g.user.id, request.path, op='Update', e_resp='Error', e_resp_msg=msg))
        flash(msg, "error")
    return redirect(url_for("brands.brand_home"))

@brands.route('/admin/brands/<int:mid>/ip/<int:ip_id>/delete', methods=['GET'])
@login_required
def delete_ip(mid, ip_id):
    ip_address = BrandIP.query.get(ip_id)
    if ip_address != None:
        db.session.delete(ip_address)
        db.session.commit()
        msg = "IP deleted"
        flash(msg, "message")
        logf.AddLog(Log(brand_item.id, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp='OK', e_resp_msg=msg))
    else:
        msg = "IP does not exist"
        logf.AddLog(Log(brand_item.id, g.current_tool.id, g.user.id, request.path, op='Delete', e_resp='OK', e_resp_msg=msg))
        flash(msg, "error")
    return redirect(url_for("brands.show_edit_brand", mid=mid))

