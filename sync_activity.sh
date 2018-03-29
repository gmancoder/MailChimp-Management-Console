#!/bin/bash

cd /projects/P01889/Mailchimp_Management_App_Development/
date >> /datastore/appllog/sync_activity.log
python sync_activity.py &>> /datastore/appllog/sync_activity.log
date >> /datastore/appllog/sync_activity.log
