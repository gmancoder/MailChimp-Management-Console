#!/bin/bash

cd /projects/P01889/Mailchimp_Management_App_Development/
date >> /datastore/appllog/job_queue.log
job_queue.py &>> /datastore/appllog/job_queue.log
date >> /datastore/appllog/job_queue.log
