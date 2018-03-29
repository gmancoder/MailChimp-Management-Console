import re
import unidecode
from models.shared import db
from models.forms import *
import datetime
from flask import redirect, url_for, g, request, flash, session
from flask_login import current_user
import ajax
import db as dbf
import xml.sax.saxutils as sax
import json
from sqlalchemy import *
import pycountry
import operator

def create_country_dict():
    countries = {}
    for country in list(pycountry.countries):
        #print vars(country)
        try:
            countries[country.alpha2] = country.name
        except:
            countries[country.name] = country.name

    return countries

def state_territory_dict():
    return {'AK': 'Alaska', 'AL': 'Alabama', 'AR': 'Arkansas', 'AS': 'American Samoa', 'AZ': 'Arizona', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DC': 'District of Columbia', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'GU': 'Guam', 'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'MA': 'Massachusetts', 'MD': 'Maryland', 'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota', 'MO': 'Missouri', 'MP': 'Northern Mariana Islands', 'MS': 'Mississippi', 'MT': 'Montana', 'NA': 'National', 'NC': 'North Carolina', 'ND': 'North Dakota', 'NE': 'Nebraska', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NV': 'Nevada', 'NY': 'New York', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'PR': 'Puerto Rico', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia', 'VI': 'Virgin Islands', 'VT': 'Vermont', 'WA': 'Washington', 'WI': 'Wisconsin', 'WV': 'West Virginia', 'WY': 'Wyoming'}

def get_form_groups(form_type):
    groups = FormGroup.query.filter(FormGroup.form_type == form_type).order_by(FormGroup.rank.asc()).all()
    return groups

def draw_form(form_type, f, method, dynamic_options={}):
    form_content = ""
    required_fields = []
    groups = get_form_groups(form_type)
    if not groups or len(groups) == 0:
        fields = {}
        if form_type == "lists":
            import lists
            fields = lists.fields()
        elif form_type == "templates":
            import templates
            fields = templates.template()
        elif form_type == "template_categories":
            import templates
            fields = templates.template_category()
        elif form_type == 'emails':
            import emails
            fields = emails.email()
        elif form_type == 'segments':
            import segments
            fields = segments.segment()
        elif form_type == 'campaigns':
            import campaigns
            fields = campaigns.campaign()
        elif form_type == "ab_tests":
            import campaigns
            fields = campaigns.variate_campaign()
            
        if len(fields) > 0:
            init_form(fields, form_type)
            groups = get_form_groups(form_type)
    
    for group in groups:
        if method == "new":
            fields = group.fields.filter(FormField.create == True).order_by(FormField.rank.asc()).all()
        elif method == "update":
            fields = group.fields.filter(FormField.update == True).order_by(FormField.rank.asc()).all()
        else:
            return ""
        if len(fields) > 0:
            if group.fieldset_on_form:
                form_content = """%s
                <fieldset id="%s">
                    <legend>%s</legend>""" % (form_content, group.id, group.name)
            for field in group.fields:
                #print field.rank
                field_value = ""
                alt_field_name = '%s_%s' % (form_type, field.name)
                if field.name in f:
                    field_value = f[field.name]
                elif alt_field_name in f:
                    field_value = f[alt_field_name]
                elif field.default_value != None:
                    field_value = field.default_value
                input_field = ""
                required = ""
                field_name = '%s_%s' % (form_type, field.name)
                if field.required:
                    required = "required"
                    required_fields.append(field_name)
                if field.tag == "input":
                    classes = ""
                    maxlength = ""
                    if field.field_type == "checkbox":
                        classes = " sw-checkbox"
                        if field_value != False:
                            maxlength = " checked "
                            field_value == "1"
                        else:
                            field_value == "0"
                    elif field.field_type == "text":
                        maxlength = " maxlength='%s' " % field.max_length
                    input_field = '<input type="%s" name="%s" id="%s" class="form-control %s" value="%s" %s %s />' % (field.field_type, field_name, field_name, classes, field_value, maxlength, required)
                elif field.tag == "textarea":
                    input_field = '<textarea name="%s" id="%s" class="form-control" style="height:100px;" %s>%s</textarea' % (field_name, field_name, field_value, required)
                elif field.tag == "select":
                    input_field = '<select name="%s" id="%s" class="form-control" %s>' % (field_name, field_name, required)
                    if field.options.count() > 0:
                        for option in field.options.order_by(FormFieldOption.label.asc()).all():
                            selected = ""
                            if (option.value == field_value) or (field_value == "None" and option.value == '0'):
                                selected = " selected"
                            input_field = '%s<option value="%s" %s>%s</option>' % (input_field, option.value, selected, option.label)
                    elif field_name in dynamic_options:
                        #print dynamic_options
                        sorted_options = sorted(dynamic_options[field_name].items(), key=(operator.itemgetter(0)))
                        for value, label in sorted_options:
                            selected = ""
                            if (str(value) == str(field_value)) or (field_value == "None" and str(value) == '0'):
                                selected = ' selected="selected"'
                            input_field = '%s<option value="%s" %s>%s</option>' % (input_field, value, selected, label)
                    input_field = '%s\n</select>' % input_field
                if input_field != "":
                    form_content = """%s
                        <div class="form-group">
                            <label for="%s" class="control-label col-lg-2">%s</label>
                            <div class="col-lg-10">
                                %s
                            </div>
                        </div>""" % (form_content, field.name, field.label, input_field)
            if group.fieldset_on_form:
                form_content = '%s</fieldset>' % form_content
    return form_content, required_fields

def init_form(fields, form_type):
    #groups = []
    for key, field in fields.items():
        if 'Form' not in field:
            group = {'Name': field['Label'], 'Rank': 0}
        else:
            group = field['Form']['Group']

        group_name = group['Name']
        group_rank = group['Rank']

        form_group = FormGroup.query.filter(and_(FormGroup.name == group_name, FormGroup.form_type == form_type)).first()
        if not form_group:
            form_group = FormGroup()
            form_group.name = group_name
            form_group.rank = group_rank
            form_group.form_type = form_type
            if group_rank == 0:
                form_group.fieldset_on_form = False
            else:
                form_group.fieldset_on_form = True
            db.session.add(form_group)
            db.session.commit()

        form_field = FormField()
        form_field.name = key
        form_field.group_id = form_group.id
        form_field.label = field['Label']
        form_field.required = field['Required']
        form_field.create = False
        form_field.update = False
        form_field.rank = 0
        if 'Form' in field:
            field_form = field['Form']
            form_field.create = True
            form_field.update = True
            form_field.rank = field_form['Rank']
            form_field.tag = field_form['Field']
            form_field.field_type = field_form['Type']
            if 'MaxLength' in field_form:
                form_field.max_length = field_form['MaxLength']
            if form_field.tag == 'select':
                for value, label in field_form['Options'].items():
                    form_field_option = create_field_option(value, label)
                    form_field.options.append(form_field_option)
        #form_group.append(form_field)
        db.session.add(form_field)
        db.session.commit()
        #groups.append(form_group)
    return True
    #return groups

def create_field_option(value, label):
    form_field_option = FormFieldOption()
    form_field_option.value = value
    form_field_option.label = label
    return form_field_option

def update_field_option(form_field_id, old_value, new_value, new_label):
    form_field = FormField.query.get(form_field_id)
    if not form_field:
        return False
    for field_option in form_field.options.get():
        if field_option.value == old_value:
            field_option.value = new_value
            field_option.label = new_label
            db.session.commit()
            return True

def get_fields_for_mapping(form_type):
    groups = get_form_groups(form_type)
    fields = []
    for group in groups:
        group_fields = group.fields.filter(or_(FormField.create == True, FormField.update == True)).order_by(FormField.required.asc(), FormField.rank.asc()).all()
        for g_field in group_fields:
            field = {'Name': g_field.name, 'Label': g_field.label, 'Required': g_field.required}
            fields.append(field)
    return fields

def get_export_fields(form_type):
    groups = get_form_groups(form_type)
    fields = []
    if len(groups) > 0:
        for group in groups:
            group_fields = group.fields.filter(FormField.export == True).order_by(FormField.required.asc(), FormField.rank.asc()).all()
            for g_field in group_fields:
                field = {'Name': g_field.name, 'Label': g_field.label, 'Required': g_field.required}
                fields.append(field)
    else:
        export_fields = []
        if form_type == 'campaign_tracking':
            import tracking
            export_fields = tracking.campaign_tracking_fields()
        elif form_type == 'ab_test_tracking':
            import tracking
            export_fields = tracking.ab_test_tracking_fields()
        
        for field in export_fields:
            new_field = {'Name': field, 'Label': field.replace('_', ' ').title(), 'Required': False}
            fields.append(new_field)

    return fields  

def get_search_fields(form_type):
    fields = []
    if 'tracking' in form_type:
        fields = [
            {'Name': 'campaign_name', 'Label': 'Campaign Name', 'Required': True},
            {'Name': 'email_name', 'Label': 'Email Name', 'Required': True},
            {'Name': 'subject_line', 'Label': 'Subject Line', 'Required': True}
        ]
    else:
        groups = get_form_groups(form_type)
        for group in groups:
            group_fields = group.fields.filter(FormField.search == True).order_by(FormField.required.asc(), FormField.rank.asc()).all()
            for g_field in group_fields:
                field = {'Name': g_field.name, 'Label': g_field.label, 'Required': g_field.required}
                fields.append(field)
    return fields        