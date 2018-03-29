#!/bin/bash

cd /projects/P01889/Mailchimp_Management_App_Development/
date >> /datastore/appllog/sync.log
python sync.py &>> /datastore/appllog/sync.log
date >> /datastore/appllog/sync.log
