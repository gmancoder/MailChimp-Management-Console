#!/usr/bin/env python
from models.shared import db
from models.imports import *
from models.exports import *
from models.tracking import *
import datetime
import os
import csv

class SystemJob(db.Model):
    __tablename__ = "system_job"
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    activity_type = db.Column(db.String(100))
    activity_id = db.Column(db.Integer)
    overall_status = db.Column(db.Integer, default=0)
    status_message = db.Column(db.String(2000), nullable=True)
    start_date = db.Column(db.TIMESTAMP, nullable=True)
    end_date = db.Column(db.TIMESTAMP, nullable=True)
    created = db.Column(db.DateTime)
    created_by = db.Column(db.String(10))
    updated = db.Column(db.DateTime)
    updated_by = db.Column(db.String(10))

    def __init__(self):
        self.created = datetime.datetime.now()
        self.updated = datetime.datetime.now()

    def run(self):
        import functions.activities as activities
        self.start_date = datetime.datetime.now()
        self.overall_status = 1
        db.session.commit()
        if self.activity_type == 'tracking_exports':
            import functions.tracking as trk
            activity = TrackingExportActivity.query.get(self.activity_id)
            if not activities.init_activity(self, activity):
                return False
            export_def = TrackingExportDefinition.query.get(activity.tracking_export_definition_id)
            if not activities.check_object(self, activity, export_def):
                return False
            
            if export_def.target_activity == '':
                activities.process_job_error(self, activity, export_def, 'Target Activity not populated');

            file_path = '%s%s' % (activities.get_ftp_path(self.brand_id, "exports"), export_def.file_path)
            try:
                ofh = open(file_path, 'w')
                writer = csv.writer(ofh, delimiter=str(export_def.file_delimiter), quoting=csv.QUOTE_ALL)
                efh = open('%s.log' % file_path, 'w')
                log_writer = csv.writer(efh, delimiter=str(export_def.file_delimiter), quoting=csv.QUOTE_ALL)
                log_writer.writerow(["Row", "RowData", "Message"])
            except Exception as e:
                activities.process_job_error(self, activity, export_def, str(e))
                return False

            status, res = trk.export_tracking_detail(export_def, writer, log_writer)

            if not status:
                activities.process_job_error(self, activity, export_def, res)
                efh.close()
                ofh.close()
                return False
            
            #Export Successful
            activity.status = 2
            self.overall_status = 2
            self.status_message = "Export Completed"
            activity.total_rows = res['total']
            activity.errors = res['errors']
            activity.end_date = datetime.datetime.now()
            self.end_date = datetime.datetime.now()
            db.session.commit()
            efh.close()
            ofh.close()
            if(export_def.notify_addresses != None and len(export_def.notify_addresses) > 0):
                status,res = activities.send_notification(export_def, self.activity_type, res)
                print res
            return True
        if self.activity_type == "exports":
            activity = ExportActivity.query.get(self.activity_id)
            if not activities.init_activity(self, activity):
                return False
            export_def = ExportDefinition.query.get(activity.export_definition_id)
            if not activities.check_object(self, activity, export_def):
                return False
            
            if export_def.fields.count() == 0:
                msg = "No Fields Passed to Export"
                activities.process_job_error(self, activity, export_def, msg)
                return False
            if export_def.target_objects.count() == 0:
                msg = "No Objects to Export"
                activities.process_job_error(self, activity, export_def, msg)
                return False

            file_path = '%s%s' % (activities.get_ftp_path(self.brand_id, "exports"), export_def.file_path)
            try:
                ofh = open(file_path, 'w')
                writer = csv.writer(ofh, delimiter=str(export_def.file_delimiter), quoting=csv.QUOTE_ALL)
                efh = open('%s.log' % file_path, 'w')
                log_writer = csv.writer(efh, delimiter=str(export_def.file_delimiter), quoting=csv.QUOTE_ALL)
                log_writer.writerow(["Row", "RowData", "Message"])
            except Exception as e:
                activities.process_job_error(self, activity, export_def, str(e))
                return False

            if export_def.target_type == "lists":
                import functions.lists as lists
                status, res = lists.export_lists(export_def, writer, log_writer)
            elif export_def.target_type == "subscribers":
                import functions.lists as lists
                status, res = lists.export_subscribers(export_def, writer, log_writer)
            elif export_def.target_type == "template_categories":
                import functions.templates as tmpl
                status, res = tmpl.export_categories(export_def, writer, log_writer)
            elif export_def.target_type == "segment_subscribers":
                import functions.segments as seg
                status, res = seg.export_subscribers(export_def, writer, log_writer)
            elif export_def.target_type == "campaign_tracking":
                import functions.tracking as trk
                status, res = trk.export_tracking_summary(export_def, writer, log_writer)
            else:
                msg = "Export target_type of '%s' not defined" % activity.target_type
                activities.process_job_error(self, activity, export_def, msg)
                efh.close()
                ofh.close()
                return False

            if not status:
                activities.process_job_error(self, activity, export_def, msg)
                efh.close()
                ofh.close()
                return False
            
            #Export Successful
            activity.status = 2
            self.overall_status = 2
            self.status_message = "Export Completed"
            activity.total_rows = res['total']
            activity.errors = res['errors']
            activity.end_date = datetime.datetime.now()
            self.end_date = datetime.datetime.now()
            db.session.commit()
            efh.close()
            ofh.close()
            if(export_def.notify_addresses != None and len(export_def.notify_addresses) > 0):
                status,res = activities.send_notification(export_def, self.activity_type, res)
                print res
            return True

        elif self.activity_type == "imports":
            activity = ImportActivity.query.get(self.activity_id)
            if not activities.init_activity(self, activity):
                return False
            
            import_def = ImportDefinition.query.get(activity.import_definition_id)
            if not activities.check_object(self, activity, import_def):
                return False

            file_path = '%s%s' % (activities.get_ftp_path(self.brand_id, "imports"), import_def.file_path)
            if not os.path.exists(file_path):
                msg = "File '%s' Not Found" % file_path
                activities.process_job_error(self, activity, import_def, msg)
                return False

            try:
                fh = open(file_path, 'r')
                reader = csv.reader(fh, delimiter=str(import_def.file_delimiter), quoting=csv.QUOTE_ALL)
                ofh = open('%s.log' % file_path, 'w')
                writer = csv.writer(ofh, delimiter=",", quoting=csv.QUOTE_ALL)
                writer.writerow(["Row", "RowData", "Message"])
            except Exception as e:
                msg = str(e)
                activities.process_job_error(self, activity, import_def, msg)
                #fh.close()
                #ofh.close()
                return False

            if import_def.mappings.count() == 0:
                msg = "Import contains no mappings"
                writer.writerow(["0", "", msg])
                activities.process_job_error(self, activity, import_def, msg)
                fh.close()
                ofh.close()
                return False

            if import_def.target_type == "lists":
                import functions.lists as lists
                status, res = lists.import_lists(import_def, reader, writer)
            elif import_def.target_type == "subscribers":
                import functions.lists as lists
                status, res = lists.import_subscribers(import_def, reader, writer)
            elif import_def.target_type == "template_categories":
                import functions.templates as tmpl
                status, res = tmpl.import_categories(import_def, reader, writer)
            else:
                msg = "Import target_type of '%s' not defined" % activity.target_type
                writer.writerow(["0", "", msg])
                activities.process_job_error(self, activity, import_def, msg)
                fh.close()
                ofh.close()
                return False

            if not status:
                writer.writerow(["0", "", res])
                activities.process_job_error(self, activity, import_def, msg)
                fh.close()
                ofh.close()
                return False
            
            #Import Successful
            activity.status = 2
            self.overall_status = 2
            self.status_message = "Import Completed"
            activity.total_rows = res['total']
            activity.inserts = res['inserted']
            activity.updates = res['updated']
            activity.ignored = res['ignored']
            activity.errors = res['errors']
            activity.end_date = datetime.datetime.now()
            self.end_date = datetime.datetime.now()
            db.session.commit()
            fh.close()
            ofh.close()
            if(import_def.notify_addresses != None and len(import_def.notify_addresses) > 0):
                status,res = activities.send_notification(import_def, self.activity_type, res)
                print res
            return True
        else:
            self.overall_status = 3
            self.status_message = "Activity type '%s' not defined" % self.activity_type
            self.end_date = datetime.datetime.now()
            db.session.commit()
            return False


