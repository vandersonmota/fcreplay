#!/bin/bash
functions="check_for_replay destroy_fcreplay" 
for f in $functions; do 
    gcloud functions deploy $f --entry-point $f --runtime python37 --trigger-http --source=./ --service-account=fcrecorder-compute-account@fcrecorder.iam.gserviceaccount.com
    if [ $? -gt 0 ]; then
        exit 1
    fi
done
exit 0