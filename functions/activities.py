#!/usr/bin/env python
from models.shared import db
from models.imports import *
from models.exports import *
from models.data_views import *
from models.list_subscribers import *
from models.tracking import *
#from models.system_jobs import *
from sqlalchemy import *
import core as f
import forms
import glob
import os
import csv
import folders
import inflection
import datetime

def init_activity(job, activity):
    if not activity:
        job.overall_status = 3
        job.status_message = "%s Activity with ID %s not found" % (inflection.singularize(job.activity_type).title(), job.activity_id)
        job.end_date = datetime.datetime.now()
        db.session.commit()
        return False
    elif activity.status != 0:
        job.overall_status = 3
        job.status_message = "Current Activity currently running or already completed"
        job.end_date = datetime.datetime.now()
        db.session.commit()
        return False
    activity.start_date = datetime.datetime.now()
    activity.status = 1
    db.session.commit()
    return True

def check_object(job, activity, obj):
    if not obj:
        activity.end_date = datetime.datetime.now()
        activity.status = 3
        job.overall_status = 3
        job.status_message = "%s Definition not found" % inflection.singularize(job.activity_type).title()
        job.end_date = datetime.datetime.now()
        db.session.commit()
        return False
    return True

def process_job_error(job, activity, activity_definition, msg):
    activity.end_date = datetime.datetime.now()
    activity.status = 3
    job.overall_status = 3
    job.status_message = msg
    if(activity_definition.notify_addresses != None and len(activity_definition.notify_addresses) > 0):
        send_notification(activity_definition, job.activity_type, {}, False, msg, True)
    job.end_date = datetime.datetime.now()
    db.session.commit()

def get_ftp_path(brand_id, activity_type):
    path = f.GetRoot();
    root_path = '%sftp/%s/%s/' % (path, brand_id, activity_type)
    return root_path

def get_import_folders(brand_id):
    root_path = get_ftp_path(brand_id, "imports")
    return _get_import_files_recursive(root_path, root_path)

def _get_import_files_recursive(path, root):
    files = []
    if not path.endswith('/'):
        path = '%s/' % path
    print path
    files_folders = glob.glob('%s*' % path)
    print files_folders
    for file in files_folders:
        path_spl = file.split('/')
        if os.path.isdir(file):
            f = {'name': path_spl[-1], 'type': 'folder', 'children': _get_import_files_recursive(file, root)}
            files.append(f)
        elif file[-4:] in ('.csv', '.tab'):
            f = {'name': path_spl[-1], 'type': 'file', 'full_path': file.replace(root, '')}
            files.append(f)
    return files

def send_notification(activity_definition, activity_definition_type, results, show_results=True, additional_content="", failed=False):
    brand = f.GetBrandByID(activity_definition.brand_id)
    if hasattr(activity_definition, 'target_folder_id'):
        status, target_folder = folders.get_folders(brand.id, activity_definition.target_folder_id, None)
    else:
        status = True
        target_folder = ""
    sub = "Notification"
    if failed:
        sub = 'FAILED'
    if activity_definition_type == 'tracking_exports':
        subject = "%s %s %s" % (brand.client, inflection.singularize(activity_definition_type.replace('_', ' ').title()), sub)
    else:
        subject = "%s %s %s %s" % (brand.client, inflection.singularize(activity_definition.target_type.replace('_', ' ').title()), inflection.singularize(activity_definition_type.replace('_', ' ').title()), sub)
    from_alias = from_email = "mmc@hometowncomputerny.com"
    content = "The following %s has completed on %s\n\n" % (inflection.singularize(activity_definition_type), datetime.datetime.now())
    content = '%sName: %s\n' % (content, activity_definition.name)
    if activity_definition_type == "imports":
        content = '%sSource: %s\n' % (content, activity_definition.file_path)
        if status:
            content = '%sDestination: %s\n\n' % (content, target_folder[0]['name'])
    elif activity_definition_type == "exports":
        content = '%sSource: %s\n' % (content, target_folder[0]['name'])
        content = '%sDestination: %s\n\n' % (content, activity_definition.file_path)
    elif activity_definition_type == 'tracking_exports':
        content = '%sSource: %ss\n' % (content, activity_definition.target_activity.title())
        content = '%sDestination: %s\n\n' % (content, activity_definition.file_path)
    if show_results:
        content = '%sRESULTS: \n' % content
        if 'total' in results:
            content = '%sTotal Records: %s\n\n' % (content, results['total'])
        for key, value in results.items():
            if key != 'total':
                content = '%s%s: %s\n' % (content, key.title(), value)
    
    if ('errors' in results and results['errors'] > 0) or ('ignored' in results and results['ignored'] > 0):
    	content = '%s\nRecords ignored or errors encountered have been logged to a delimited text file named %s.log and stored in the same folder as the source file' % (content, activity_definition.file_path)

    if additional_content != "":
        content = '%s\n\nAdditional Information:\n%s' % (content, additional_content)
    try:
        f.SendEmail(from_email, from_alias, activity_definition.notify_addresses, subject, content)
        return True, "Email Sent"
    except Exception as e:
        return False, str(e)

def setup_import_mapping(brand_id, target_folder_id, target_type, import_file, import_file_delimiter):
    if target_type == 'subscribers':
        import lists
        fields = lists.subscriber_import_mapping(target_folder_id)
    else:
        fields = forms.get_fields_for_mapping(target_type)
    headers = []
    root_path = get_ftp_path(brand_id, "imports")
    import_file_path = '%s%s' % (root_path, import_file)
    if os.path.exists(import_file_path):
        fh = open(import_file_path, 'r')
        reader = csv.reader(fh, delimiter=str(import_file_delimiter))
        row_count = sum(1 for row in reader)
        if row_count < 2:
            return False, "Empty File", ""
        idx = 0
        fh.seek(0)
        for row in reader:
            if idx == 0:
                header_row = row
            elif idx == 1:
                sample_row = row
            else:
                break
            idx += 1
        
        for idx in range(0, len(header_row)):
            header = {}
            header['name'] = header_row[idx]
            header['sample'] = sample_row[idx]
            headers.append(header)
    return True, headers, fields

def get_import_definition(import_def_id):
    import_def = ImportDefinition.query.get(import_def_id)
    return import_def

def create_import_definition(brand, name, folder_id, target_type, import_file, import_file_delimiter, import_type, import_notification, mapping, user, system_def=False, target_folder_id=None, target_list_id=None):
    import_def = ImportDefinition()
    import_def.brand_id = brand
    import_def.name = name
    if folder_id == "":
        root_folder = folders.get_root_folder(brand, "imports")
        import_def.folder_id = root_folder.id
    else:
        import_def.folder_id = folder_id
    import_def.file_path = import_file
    import_def.file_delimiter = import_file_delimiter
    import_def.target_type = target_type
    import_def.target_folder_id = target_folder_id
    import_def.target_list_id = target_list_id
    import_def.import_type = import_type
    import_def.system_definition = system_def
    import_def.notify_addresses = import_notification
    import_def.created_by = user.id
    import_def.updated_by = user.id
    for m in mapping:
        import_mapping = ImportFieldMapping()
        import_map = m.split(':')
        import_mapping.source_field = import_map[0]
        import_mapping.destination_field = import_map[1]
        import_mapping.created_by = user.id
        import_mapping.updated_by = user.id
        import_def.mappings.append(import_mapping)

    try:
        db.session.add(import_def)
        db.session.commit()
        return True, import_def
    except Exception as e:
        return False, str(e)

def get_export_definition(export_def_id):
    return ExportDefinition.query.get(export_def_id)

def create_export_definition(brand, name, folder_id, target_type, target_folder_id, export_file, export_file_delimiter, export_type, export_notification, fields, target_objects, user, system_def):
    export_def = ExportDefinition()
    export_def.brand_id = brand
    export_def.name = name
    if folder_id == "":
        root_folder = folders.get_root_folder(brand, "exports")
        export_def.folder_id = root_folder.id
    else:
        export_def.folder_id = folder_id
    export_def.file_path = export_file
    export_def.file_delimiter = export_file_delimiter
    export_def.target_type = target_type
    if target_type == "subscribers":
        export_def.target_list_id = target_folder_id
    elif target_type == "segment_subscribers":
        export_def.target_segment_id = target_folder_id
    else:
        export_def.target_folder_id = target_folder_id
    export_def.export_type = export_type
    export_def.system_definition = system_def
    export_def.notify_addresses = export_notification
    export_def.created_by = user.id
    export_def.updated_by = user.id

    for field in fields:
        export_field = ExportField()
        export_field.field_name = field
        export_field.created_by = user.id
        export_field.updated_by = user.id
        export_def.fields.append(export_field)

    for obj in target_objects:
        export_object = ExportObject()
        export_object.object_id = obj
        export_object.created_by = user.id
        export_object.updated_by = user.id
        export_def.target_objects.append(export_object)

    try:
        db.session.add(export_def)
        db.session.commit()
        return True, export_def
    except Exception as e:
        return False, str(e)

def get_tracking_export_definition(tracking_export_def_id):
    return TrackingExportDefinition.query.get(tracking_export_def_id)

def create_tracking_export_definition(brand, name, folder_id, target_type, target_activity, target_id, export_file, export_file_delimiter, export_notification, user, system_def):
    export_def = TrackingExportDefinition()
    export_def.brand_id = brand
    export_def.name = name
    if folder_id == "":
        root_folder = folders.get_root_folder(brand, "tracking_exports")
        export_def.folder_id = root_folder.id
    else:
        export_def.folder_id = folder_id
    export_def.file_path = export_file
    export_def.file_delimiter = export_file_delimiter
    export_def.target_id = target_id
    export_def.target_activity = target_activity
    export_def.target_type = target_type
    export_def.system_definition = system_def
    export_def.notify_addresses = export_notification
    export_def.created_by = user.id
    export_def.updated_by = user.id

    try:
        db.session.add(export_def)
        db.session.commit()
        return True, export_def
    except Exception as e:
        return False, str(e)

def create_import_activity(import_definition_id, user):
    import_activity = ImportActivity()
    import_activity.import_definition_id = import_definition_id
    import_activity.created_by = user.id
    import_activity.updated_by = user.id
    try:
        db.session.add(import_activity)
        db.session.commit()
        return True, import_activity.id
    except Exception as e:
        return False, str(e)

def create_export_activity(export_definition_id, user):
    export_activity = ExportActivity()
    export_activity.export_definition_id = export_definition_id
    export_activity.created_by = user.id
    export_activity.updated_by = user.id
    try:
        db.session.add(export_activity)
        db.session.commit()
        return True, export_activity.id
    except Exception as e:
        return False, str(e)

def create_tracking_export_activity(tracking_export_definition_id, user):
    export_activity = TrackingExportActivity()
    export_activity.tracking_export_definition_id = tracking_export_definition_id
    export_activity.created_by = user.id
    export_activity.updated_by = user.id
    try:
        db.session.add(export_activity)
        db.session.commit()
        return True, export_activity.id
    except Exception as e:
        return False, str(e)

def submit_job(brand, activity_id, activity_type, user):
    import models.system_jobs as sysjob
    job = sysjob.SystemJob()
    job.brand_id = brand
    job.activity_type = activity_type
    job.activity_id = activity_id
    job.created_by = user.id
    job.updated_by = user.id
    try:
        db.session.add(job)
        db.session.commit()
        return True, job.id
    except Exception as e:
        return False, str(e)

def api_submit_import(brand, name, folder_id, target_type, target_folder_id, import_file, import_file_delimiter, import_type, import_notification, mapping, user, system_def):
    if target_type == "subscribers":
        status, import_def = create_import_definition(brand, name, folder_id, target_type, import_file, import_file_delimiter, import_type, import_notification, mapping, user, system_def, target_list_id=target_folder_id)
    else:
        status, import_def = create_import_definition(brand, name, folder_id, target_type, import_file, import_file_delimiter, import_type, import_notification, mapping, user, system_def, target_folder_id=target_folder_id)
    if not status:
        return False, import_def

    status, activity_id = create_import_activity(import_def.id, user)
    if not status:
        return False, activity_id

    status, job_id = submit_job(brand, activity_id, "imports", user)
    if not status:
        return False, job_id

    return True, {'Import Definition ID': import_def.id, 'Import Activity ID': activity_id, 'Job ID': job_id}

def get_mapped_field(fld, mappings, id):
    field = mappings.filter(and_(ImportFieldMapping.import_definition_id == id, ImportFieldMapping.source_field == fld)).first()
    if field:
        return field.destination_field
    return None

def api_submit_export(brand, name, folder_id, target_type, target_folder_id, export_file, export_file_delimiter, export_type, export_notification, fields, target_objects, user, system_def):
    if target_type == "lists" and export_type in ('1', '3'):
        import lists
        if export_type == '3':
            target_lists = lists.lists_in_folder(target_folder_id)
        elif export_type == '1':
            target_lists = lists.get_all(brand)
        for list in target_lists:
            target_objects.append(list.id)
    elif target_type == "subscribers" and export_type == "1":
        import lists
        status, target_objects = lists.get_subscriber_ids_for_export(target_folder_id)
        if not status:
            return False, target_objects
    elif target_type == "segment_subscribers" and export_type == "1":
        import segments
        status, target_objects = segments.get_subscriber_ids_for_export(brand, target_folder_id)
        if not status:
            return False, target_objects
    elif target_type == "template_categories" and export_type in ('1', '3'):
        import templates
        if export_type == '3':
            target_template_categories = templates.template_categories_in_folder(target_folder_id)
        elif export_type == '1':
            target_template_categories = templates.get_all(brand)
        for template_category in target_template_categories:
            target_objects.append(template_category.id)
    elif target_type == "campaign_tracking" and export_type in ('1', '3'):
        import tracking
        if export_type == '3':
            target_tracking = tracking.tracking_in_folder(target_folder_id)
        elif export_type == '1':
            target_tracking = tracking.get_all(brand, "campaigns")
        for tracked in target_tracking:
            target_objects.append(tracked.id)
    status, export_def = create_export_definition(brand, name, folder_id, target_type, target_folder_id, export_file, export_file_delimiter, export_type, export_notification, fields, target_objects, user, system_def)
    if not status:
        return False, export_def

    status, activity_id = create_export_activity(export_def.id, user)
    if not status:
        return False, activity_id

    status, job_id = submit_job(brand, activity_id, "exports", user)
    if not status:
        return False, job_id

    return True, {'Export Definition ID': export_def.id, 'Export Activity ID': activity_id, 'Job ID': job_id}

def api_submit_tracking_export(brand, name, folder_id, target_type, target_activity, target_id, export_file, export_file_delimiter, export_notification, user, system_def):
    status, export_def = create_tracking_export_definition(brand, name, folder_id, target_type, target_activity, target_id, export_file, export_file_delimiter, export_notification, user, system_def)
    if not status:
        return False, export_def

    status, activity_id = create_tracking_export_activity(export_def.id, user)
    if not status:
        return False, activity_id

    status, job_id = submit_job(brand, activity_id, "tracking_exports", user)
    if not status:
        return False, job_id

    return True, {'Export Definition ID': export_def.id, 'Export Activity ID': activity_id, 'Job ID': job_id}
def sync_data_views():
    errors = []
    DataView_Sent.query.delete()
    DataView_Bounce.query.delete()
    DataView_Open.query.delete()
    DataView_Click.query.delete()
    DataView_Unsubscribe.query.delete()
    all_subscribers = ListSubscriber.query.all()
    for subscriber in all_subscribers:
        email_id = subscriber.email_id
        email_address = subscriber.email_address
        unique_email_id = subscriber.unique_email_id
        brand_id = subscriber.brand_id
        list_id = subscriber.list_id
        for activity in subscriber.activity.all():
            if activity.action == 'sent':
                new_record = DataView_Sent()
            elif activity.action == 'open':
                new_record = DataView_Open()
            elif activity.action == 'click':
                new_record = DataView_Click()
                new_record.url = activity.url
            elif activity.action == 'bounce':
                new_record = DataView_Bounce()
                new_record.bounce_type = activity.type
            elif activity.action == 'unsub':
                new_record = DataView_Unsubscribe()
                new_record.unsubscribe_type = activity.type
            new_record.brand_id = brand_id
            new_record.campaign_id = activity.campaign_id
            new_record.email_id = email_id
            new_record.email_address = email_address
            new_record.unique_email_id = unique_email_id
            new_record.list_id = list_id
            new_record.event_date = activity.timestamp
            new_record.campaign_title = activity.title
            try:
                db.session.add(new_record)
                db.session.commit()
            except Exception as ex:
                errors.append(str(ex))
    return errors
