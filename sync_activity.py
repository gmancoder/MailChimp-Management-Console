#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mailchimp import app, db
from sqlalchemy import *
import functions.core as f
import functions.lists as lists
import functions.brands as brands
import functions.users as users
import functions.folders as folders
import functions.activities as activities
import functions.tracking as tracking
import tools.tools as tools
import tools.logger as logger
import os
import sys
import json
import unidecode
import datetime
import optparse
import time
SYNC_USER_ID = 2
MC_RECORDS_PER_PAGE = 10
def GetArgsOptions():
    parser = optparse.OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="print log to screen while processing", default=False)
    parser.add_option("-d", "--date", action="store", dest="last_run", help="pull subscriber activity for lists sent to since this date", default=get_last_run())
    return parser.parse_args()

def get_last_run():
    last_run = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y%m%d %H:%M:%S')
    return last_run

def sync_list_subscriber_activity(brand, last_sent, errors, user):
    all_lists = lists.get_all_last_sent(brand.id, last_sent)
    for mmc_list in all_lists:
        list_id = mmc_list.mailchimp_id
        for mc_subscriber in mmc_list.subscribers.all():
            total_activity = 10
            idx3 = 0
            while True:
                if idx3 > total_activity or total_activity == 0:
                    break
                status, activity_response = f.post_to_mailchimp(brand, "lists/%s/members/%s/activity?offset=%d" % (list_id, mc_subscriber.email_id, idx3), method="GET")
                if not status:
                    error = {'Method': 'ListMemberActivity-Get', 'Error': activity_response}
                    errors.append(error)
                    break
                else:
                    mc_subscriber_activity = json.loads(activity_response)
                    if idx3 == 0:
                        total_activity = mc_subscriber_activity['total_items']
                    idx3 += MC_RECORDS_PER_PAGE
                    for activity in mc_subscriber_activity['activity']:
                        action = activity['action']
                        timestamp = activity['timestamp']
                        campaign_mailchimp_id = activity['campaign_id']
                        title = activity['title']
                        activity_type = None
                        url = None
                        if 'type' in activity:
                            activity_type = activity['type']
                        if 'url' in activity:
                            url = activity['url']
                        status, response = lists.post_subscriber_activity(brand.id, mc_subscriber.id, action, timestamp, url, activity_type, campaign_mailchimp_id, title, user)
                        if not status:
                            error = {'Method': 'ListMemberActivity-Post', 'Error': response}
                            errors.append(error)
    return errors

if __name__ == '__main__':
    options, args = GetArgsOptions();
    log = logger.Logger('mmc_sub_activity_sync')
    log.SetPrintToScreen(options.verbose)
    log.LogInfo("Last Run: %s" % str(options.last_run))
    with app.app_context():
        errors = []
        user = users.user_by_id(SYNC_USER_ID)
        all_brands = brands.all_brands()
        log.LogInfo('Processing List Subscriber Activity')
        for brand in all_brands:
            # List Subscriber Activity
            errors = sync_list_subscriber_activity(brand, str(options.last_run), errors, user)
            for error in errors:
                log.LogError('%(Method)s - %(Error)s' % error) 
        #log.LogInfo('Processing Data Views')
        #errors = activities.sync_data_views()
        #for error in errors:
        #    log.LogError('%(Method)s - %(Error)s' % error)
        log.LogInfo('Processing Tracking')
        errors = tracking.sync_tracking()
        for error in errors:
            log.LogError('%(Method)s - %(Error)s' % error)
    log.Close(0, '')
