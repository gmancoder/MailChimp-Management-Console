#!/bin/bash

cd /projects/P01889/Mailchimp_Management_App_Development/
date >> /datastore/appllog/sync_activity.log
python sync_activity.py --date="19820518 08:00:00" &>> /datastore/appllog/sync_activity.log
date >> /datastore/appllog/sync_activity.log
