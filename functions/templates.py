#!/usr/bin/env python
from models.shared import db
from models.templates import *
from models.folders import *
from models.forms import *
from models.users import *
import activities
import core as f
import forms
import json
import datetime
import folders
from sqlalchemy import *
from sqlalchemy import func
import bs4

def template_category():
    fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'Name', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 1},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }}
    }
    return fields

def template():
    fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'Name', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'category_id': {'Label': 'Category', 'Required': False, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'select',
        'Type': 'select',
        'Rank': 2,
        'Options': {}
        }},
    'active': {'Label': 'Active', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'input',
        'Type': 'checkbox',
        'Rank': 3
        }},
    'html': {'Label': 'HTML', 'Required': True}
    }

    return fields

def all_templates(brand_id):
    return Template.query.filter(Template.brand_id == brand_id).all()

def all_templates_id_dict(brand_id):
    templates = all_templates(brand_id)
    template_dict = {}
    for template in templates:
        template_dict[str(template.id)] = template.name
    return template_dict

def template_by_id(brand_id, template_id):
    template = Template.query.filter(and_(Template.brand_id == brand_id, Template.id == template_id)).first()
    if not template:
        return False, "Template not found"
    return True, template

def template_by_mailchimp_id(brand_id, template_id):
    template = Template.query.filter(and_(Template.brand_id == brand_id, Template.mailchimp_id == template_id)).first()
    if not template:
        return False, "Template not found"
    return True, template

def template_to_db(brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, user, html="", sections=None, id=None):
    if id == None:
        return add_template_to_db(brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, user, html, sections)
    else:
        return update_template_to_db(id, brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, user, html, sections)


def add_template_to_db(brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, user, html="", sections=None):
    new_template = Template()
    new_template = template_fields_to_obj(new_template, brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, html)
    new_template.created_by = user.id
    try:
        db.session.add(new_template)
        db.session.commit()
        if sections != None:
            status, response = add_sections_to_template_db(new_template.id, sections)
            if not status:
                return False, response
        return True, f._obj_to_dict([new_template])
    except Exception as e:
        return False, str(e)

def update_template_to_db(template_id, brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, user, html="", sections=None):
    new_template = Template.query.get(template_id)
    if not new_template:
        return False, "Template not found"

    new_template = template_fields_to_obj(new_template, brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, html)
    new_template.updated = datetime.datetime.now()
    new_template.updated_by = user.id
    try:
        db.session.commit()
        if sections != None:
            status, response = delete_sections_from_db(new_template.sections.all())
            if not status:
                return False, response
            status, response = add_sections_to_template_db(new_template.id, sections)
            if not status:
                return False, response
        return True, f._obj_to_dict([new_template])
    except Exception as e:
        return False, str(e)

def template_fields_to_obj(new_template, brand_id, category_id, folder_id, mailchimp_id, name, type, active, thumbnail, html=""):
    new_template.brand_id = int(brand_id)
    if category_id != "" and category_id != None:
        new_template.category_id = int(category_id)
    new_template.folder_id = int(folder_id)
    new_template.mailchimp_id = mailchimp_id
    new_template.name = name
    new_template.type = type
    new_template.active = active
    new_template.thumbnail = thumbnail
    if html != "":
        new_template.html = html

    return new_template

def add_sections_to_template_db(template_id, sections):
    for tag,default_content in sections.items():
        section = TemplateSection()
        section.template_id = template_id
        section.tag = tag
        section.default_content = default_content
        try:
            db.session.add(section)
            db.session.commit()
        except Exception as e:
            return False, str(e)
    return True, "OK"

def delete_sections_from_db(template_sections):
    for section in template_sections:
        try:
            db.session.delete(section)
            db.session.commit()
        except Exception as e:
            return False, str(e)
    return True, "OK"

def template_to_request(template):
    template_request = {}
    template_request['templates_name'] = template.name
    template_request['templates_category_id'] = template.category_id
    template_request['templates_active'] = template.active
    return template_request

def template_to_mailchimp(brand_id, folder_id, name, category_id, active, html="", mailchimp_id=None):
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Brand not found"
    status, folder = folders.get_folder_by_id(brand_id, folder_id)
    if not status:
        return False, folder
    data = {'name': name}

    if folder.mailchimp_id != None:
        data['folder_id'] = folder.mailchimp_id

    if mailchimp_id == None:
        data['html'] = "<p></p>"
        return f.post_to_mailchimp(brand, "templates", json.dumps(data))
    else:
        data['html'] = html
        return f.patch_to_mailchimp(brand, "templates", json.dumps(data), mailchimp_id)

def get_template_sections(brand_id, id):
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Brand not found"
    data_type = 'templates/%s/default-content' % id
    return f.post_to_mailchimp(brand, data_type, None, method="GET")

def template_sections(brand_id, template_id):
    sections = []
    template = Template.query.filter(and_(Template.brand_id == brand_id, Template.id == template_id)).first()
    if template:
        sections = template.sections.all()
    return sections

def parse_template_sections(template):
    if template.html != "":
        soup = bs4.BeautifulSoup(template.html, 'html.parser')
        sections = parse_template_sections_r(soup.html.body, {})
        return sections
    return {}

def parse_template_sections_r(tag, sections):
    if tag.name != None:
        if 'mc:edit' in tag.attrs:
            sections[tag['mc:edit']] = {'Name': tag.name, 'Content': str(tag)}
        for content in tag.contents:
            sections = parse_template_sections_r(content, sections)
    return sections
def save_html(brand_id, template_id, content, user):
    brand = f.GetBrandByID(brand_id)
    if not brand:
        return False, "Brand not found"
    template = Template.query.filter(Template.brand_id == brand_id, Template.id == template_id).first()
    if not template:
        return False, "Template not found"
    
    data = {'name': template.name, 'html': content}
    status, response = f.patch_to_mailchimp(brand, "templates", json.dumps(data), template.mailchimp_id)
    if not status:
        return False, response
    
    try:
        j_response = json.loads(response)
        status, section_response = get_template_sections(brand_id, template.mailchimp_id)
        if not status:
            return False, section_response
        j_section_response = json.loads(section_response)
        if len(j_section_response['sections']) > 0:
            sections = j_section_response['sections']
            status, response = delete_sections_from_db(template.sections.all())
            if not status:
                return False, response
            status, response = add_sections_to_template_db(template.id, sections)
            if not status:
                return False, response
        template.thumbnail = j_response['thumbnail']
        template.html = content
        template.updated_by = user.id
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def move_template(brand_id, template_id, folder_id, user):
	template = Template.query.filter(and_(Template.brand_id == brand_id, Template.id == template_id)).first()
	if not template:
		return False, "Template not found"
	status, response = template_to_mailchimp(brand_id, folder_id, template.name, template.category_id, template.active, template.html, template.mailchimp_id)
	if not status:
		return False, response

	return template_to_db(brand_id, template.category_id, folder_id, template.mailchimp_id, template.name, template.type, template.active, template.thumbnail, user, template.html, id=template_id)

def delete_template(brand_id, template_id):
	brand = f.GetBrandByID(brand_id)
	if not brand:
		return False, "Brand not found"
	template = Template.query.filter(and_(Template.brand_id == brand_id, Template.id == template_id)).first()
	if not template:
		return False, "Template not found"
	status, response = f.delete_to_mailchimp(brand, "templates", template.mailchimp_id)
	if not status:
		return False, response

	try:
		db.session.delete(template)
		db.session.commit()
		return True, "OK"
	except Exception as ex:
		return False, str(ex)

def template_category_exists(brand_id, name, update=False):
    count = TemplateCategory.query.filter(and_(TemplateCategory.brand_id == brand_id, TemplateCategory.name == name)).count()
    return count > 0

def add_template_category(brand_id, name, folder_id, user_id, sync=False):
    template_category = TemplateCategory()
    template_category.brand_id = brand_id
    template_category.name = name
    template_category.folder_id = folder_id
    template_category.created_by = user_id
    try:
        db.session.add(template_category)
        db.session.commit()
        if sync:
            return True, template_category
        return True, f._obj_to_dict([template_category])
    except Exception as e:
        return False, str(e)

def get_template_category_field():
    form_groups = forms.get_form_groups('templates')
    form_field_id = None
    for group in form_groups:
        form_fields = group.fields.all()
        for form_field in form_fields:
            if form_field.name == 'Category':
                form_field_id = form_field.id
                break
        if form_field_id != None:
            break
    return form_field_id

def add_template_category_option(name):
    form_field_id = get_template_category_field()
    if form_field_id != None:
        form_field_option = forms.create_field_option(name, name)
        form_field_option.form_field_id = form_field_id
        try:
            db.session.add(form_field_option)
            db.session.commit()
            return True, "OK"
        except Exception as ex:
            return False, str(ex)
    else:
        return False, "Form Field Not Found"

def get_template_category_by_name(brand_id, name, sync=False):
    template_category_query = TemplateCategory.query.filter(and_(TemplateCategory.brand_id == brand_id, TemplateCategory.name == name)).first()
    if template_category_query.count() == 0:
        return True, []
    if sync:
        return True, template_category_query.all()
    return True, f._obj_to_dict(template_category_query.all())

def get_template_category_by_id(brand_id, template_category_id):
    template_category = TemplateCategory.query.filter(and_(TemplateCategory.brand_id == brand_id, TemplateCategory.id == template_category_id)).first()
    if not template_category:
        return False, "Template Category Not Found"
    return template_category


def template_categories_in_folder(folder_id):
    return TemplateCategory.query.filter(TemplateCategory.folder_id == folder_id).all()

def get_all(brand_id):
    return TemplateCategory.query.filter(TemplateCategory.brand_id == brand_id).all()

def get_all_dict(brand_id):
    categories = {}
    all_categories = get_all(brand_id)
    for category in all_categories:
        categories[str(category.id)] = category.name
    return categories

def update_template_category(template_category, name, user_id):
    old_name = template_category.name
    template_category.name = name
    template_category.updated_by = user_id
    try:
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def update_template_category_option(old_name, name):
    form_field_id = get_template_category_field()
    if form_field_id != None:
        return forms.update_field_option(form_field_id, old_name, name, name)
    return False

def move_category(category_id, to_folder_id):
    category = TemplateCategory.query.get(category_id)
    if not category:
        return False, "Template Category not found"
    category.folder_id = to_folder_id
    try:
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def delete_category(brand_id, id):
    template_category = TemplateCategory.query.get(id)
    if not template_category:
        return False, "Category not found"
    try:
        db.session.delete(template_category)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def import_categories(import_def, reader, writer):
    brand = f.GetBrandByID(import_def.brand_id)
    user = User.query.get(import_def.created_by)
    results = {'total': 0, 'inserted': 0, 'updated': 0, 'ignored': 0, 'errors': 0}
    if not brand:
        return False, "Brand not found"
    if not user:
        return False, "User not found"
    headers = {}
    row_count = 0
    for row in reader:
        row_count += 1
        if row_count == 1:
            for fld in range(0, len(row)):
                header = row[fld]
                dest = activities.get_mapped_field(header, import_def.mappings, import_def.id)
                if dest != None:
                    headers[header] = {'idx': fld, 'dest': dest}
            continue
        results['total'] += 1
        name_idx = headers['name']['idx']
        existing = template_category_exists(import_def.brand_id, row[name_idx])
        if import_def.import_type == 2:
            if existing:
                results['ignored'] += 1
                writer.writerow([row_count, ','.join(row), "Template Category '%s' already exists" % row[name_idx]])
                continue
        elif import_def.import_type == 3:
            if not existing:
                results['ignored'] += 1
                writer.writerow([row_count, ','.join(row), "Template Category '%s' does not exist" % row[name_idx]])
                continue
        else:
            request = {}
            for src, header in headers.items():
                request_col = 'template_categories_%s' % header['dest']
                request[request_col] = row[header['idx']]
            if not existing:
                status, resp = add_template_category(brand.id, row[name_idx], import_def.target_folder_id, user.id)
                if status:
                    results['inserted'] += 1
                else:
                    msg = 'DB Create Failed: %s' % resp
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), msg])
            else:
                current_category = TemplateCategory.query.filter(and_(TemplateCategory.brand_id == brand.id, TemplateCategory.name == row[name_idx])).first()
                if not current_category:
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), "Template Category '%s' not found" % row[name_idx]])
                    continue
                
                status, resp = update_template_category(current_category, row[name_idx], user.id)
                if status:
                    results['updated'] += 1
                else:
                    msg = 'DB Update Failed: %s' % resp
                    results['errors'] += 1
                    writer.writerow([row_count, ','.join(row), msg])
    return True, results

def export_categories(export_def, writer, log_writer):
    fields = []
    objects = []
    results = {'total': 0, 'errors': 0}
    for field in export_def.fields.all():
        fields.append(field.field_name)

    for obj in export_def.target_objects.all():
        objects.append(obj.object_id)

    writer.writerow(fields)
    categories = TemplateCategory.query.filter(TemplateCategory.id.in_(objects)).all()
    idx = 0
    for category in categories:
        idx += 1
        row = []
        error = False
        request = {'id': category.id, 'name': category.name}
        for field in fields:
            if field in request:
                row.append(request[field])
            else:
                error = True
                log_writer.writerow([idx, ','.join(row), '%s not a template category field' % field])
        if not error:
            writer.writerow(row)
            results['total'] += 1
        else:
            results['errors'] += 1

    return True, results

def search_categories(brand, search_type, search_for, search_contains, search_folder_id):
    fields = ['ID', 'Name', 'Folder']
    query = TemplateCategory.query
    if search_type == "2":
        query = query.filter(and_(TemplateCategory.brand_id == brand, TemplateCategory.folder_id == search_folder_id, TemplateCategory.name.like('%%%s%%' % search_contains)))
    else:
        query = query.filter(and_(TemplateCategory.brand_id == brand, TemplateCategory.name.like('%%%s%%' % search_contains)))
    query = query.order_by(TemplateCategory.name.asc()).all()

    rows = []
    for template_category in query:
        status, flds = folders.get_folders(brand, folder_id=template_category.folder_id)
        if not status:
            return False, flds
        row = {}
        row['ID'] = template_category.id
        row['Name'] = "<a href='/template_categories/%s/edit'>%s</a>" % (template_category.id, template_category.name)
        row['Folder'] = flds[0]['name']
        rows.append(row)
    return True, {'Fields': fields, 'Data': rows}


