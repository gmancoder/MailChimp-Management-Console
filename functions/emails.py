#!/usr/bin/env python
from models.shared import db
from models.emails import *
from models.folders import *
from models.forms import *
from models.users import *
import activities
import core as f
import forms
import json
import datetime
import folders
import templates
import unidecode
from sqlalchemy import *
from sqlalchemy import func

def email():
    fields = {
    'id': {'Label': 'ID', 'Required': True},
    'name': {'Label': 'Name', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 1,
        }},
    'template_id': {'Label': 'Template', 'Required': False, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'select',
        'Type': 'select',
        'Rank': 2,
        'Options': {}
        }},
    'subject': {'Label': 'Subject', 'Required': True, 'Form': {
        'Group': {'Name': 'General', 'Rank': 0},
        'Field': 'input',
        'Type': 'text',
        'MaxLength': 200,
        'Rank': 3,
        }},
    }

    return fields

def all_emails(brand_id):
    emails = Email.query.filter(Email.brand_id == brand_id).all()
    return emails

def email_to_form_dict(email):
    email_dict = {"emails_name": email.name, "emails_template_id": email.template_id, "emails_subject": email.subject}
    #emails = f._obj_to_dict([email])
    #for key, value in emails[0].items():
    #    email_dict['emails_%s' % key] = value
    return email_dict

def email_to_db(brand_id, template_id, name, subject, folder_id, user, last_sent=None, html="", id=None):
    if id == None:
        return add_email_to_db(brand_id, template_id, name, subject, folder_id, user, last_sent, html)
    else:
        return update_email_to_db(id, brand_id, template_id, name, subject, folder_id, user, last_sent, html)

def add_email_to_db(brand_id, template_id, name, subject, folder_id, user, last_sent=None, html=""):
    email = Email()
    email = email_fields_to_obj(email, brand_id, template_id, name, subject, folder_id, last_sent, html)
    email.created_by = user.id

    try:
        db.session.add(email)
        db.session.commit()
        return True, email.id
    except Exception as ex:
        return False, str(ex)

def update_email_to_db(id, brand_id, template_id, name, subject, folder_id, user, last_sent=None, html=""):
    status, email = email_by_id(brand_id, id)
    if not status:
        return False, email
    email = email_fields_to_obj(email, brand_id, template_id, name, subject, folder_id, last_sent, html)
    email.updated_by = user.id
    email.updated = datetime.datetime.now()
    try:
        db.session.commit()
        return True, email.id
    except Exception as ex:
        return False, str(ex)

def email_fields_to_obj(email, brand_id, template_id, name, subject, folder_id, last_sent, html):
    email.brand_id = brand_id
    email.template_id = template_id
    email.name = name
    email.subject = subject
    email.folder_id = folder_id
    if last_sent != None:
        email.last_sent = last_sent
    email.full_html = html

    return email

def email_sections_dict(email):
    sections = {}
    for section in email.sections.all():
        sections[section.tag] = section.content
    return sections

def email_by_id(brand, email_id):
    email = Email.query.filter(and_(Email.brand_id == brand, Email.id == email_id)).first()
    #print email
    if not email:
        return False, "Email not found"
    return True, email

def email_by_campaign_name(brand, campaign_name):
    email = Email.query.filter(and_(Email.brand_id == brand, Email.name == campaign_name)).first()
    #print email
    if not email:
        return False, "Email not found"
    return True, email

def save_html(brand, email_id, content, sections, user):
    status, email = email_by_id(brand, email_id)
    if not status:
        return False, email

    for e_section in email.sections.all():
        try:
            db.session.delete(e_section)
            db.session.commit()
        except Exception as ex:
            return False, str(ex)

    status, template = templates.template_by_id(brand, email.template_id)
    if not status:
        return False, template

    if len(sections) > 0:
        html = template.html
        email_sections = {}
        for section in sections:    
            tag, content = section.split('#||#',1)
            new_section = EmailSection()
            new_section.email_id = email_id
            new_section.tag = tag
            new_section.content = content
            try:
                db.session.add(new_section)
                db.session.commit()
            except Exception as ex:
                return False, str(ex)

            email_sections[tag] = content

        template_sections = templates.parse_template_sections(template)
        for tag, content in template_sections.items():
            html_to_replace = content['Content']
            new_tag = content['Name']
            if tag in email_sections:
                repl = '<%s>%s</%s>' % (new_tag, email_sections[tag], new_tag)
                #print html_to_replace
                #print repl
                html_to_replace = html_to_replace.decode('utf-8', 'ignore')
                repl = repl.strip()
                repl = repl.replace(u'\\xa0', '')
                repl = repl.strip()
                #repl = str(repl).decode('utf-8', 'ignore')
                try:
                    html = html.replace(html_to_replace, repl)
                except Exception as ex:
                    return False, '%s - %s' % (str(ex), tag)
                #html = html.replace(unidecode.unidecode(html_to_replace), unidecode.unidecode(repl))
        
        email.full_html = html
        email.html_by = "Template"
    else:
        email.full_html = content
        email.html_by = "Raw Content"
    try:
        email.updated = datetime.datetime.now()
        email.updated_by = user.id
        db.session.commit()
        return True, email.full_html
    except Exception as ex:
        return False, str(ex)

def search(brand, search_type, search_for, search_contains, search_folder_id):
    fields = ['ID', 'Name', 'Subject', 'Folder']
    query = Email.query
    if search_for == "name":
        if search_type == 2:
            query = query.filter(and_(Email.brand_id == brand, Email.folder_id == search_folder_id, Email.name.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(Email.brand_id == brand, Email.name.like('%%%s%%' % search_contains)))
    elif search_for == "subject":
        if search_type == 2:
            query = query.filter(and_(Email.brand_id == brand, Email.folder_id == search_folder_id, Email.subject.like('%%%s%%' % search_contains)))
        else:
            query = query.filter(and_(Email.brand_id == brand, Email.subject.like('%%%s%%' % search_contains)))
    emails = query.all()
    rows = []
    for email in emails:
        status, folder = folders.get_folder_by_id(brand, folder_id=email.folder_id)
        if not status:
            return False, folder
        row = {}
        row['ID'] = email.id
        row['Name'] = '<a href="/emails/%s/detail">%s</a>' % (email.id, email.name)
        row['Subject'] = email.subject
        row['Folder'] = folder.name
        rows.append(row)
    return True, {'Fields': fields, 'Data': rows}

def move(brand_id, email_id, folder_id, user):
    status, email = email_by_id(brand_id, email_id)
    if not status:
        return False, email

    try:
        email.folder_id = folder_id
        email.updated = datetime.datetime.now()
        email.updated_by = user.id
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)

def delete(brand_id, email_id):
    status, email = email_by_id(brand_id, email_id)
    if not status:
        return False, email

    try:
        db.session.delete(email)
        db.session.commit()
        return True, "OK"
    except Exception as ex:
        return False, str(ex)
