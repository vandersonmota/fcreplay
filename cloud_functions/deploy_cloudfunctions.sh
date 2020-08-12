#!/bin/bash
functions="check_for_replay destroy_fcreplay video_status"

# Get config
cp ../config.json ./

# Get service account
SERVICE_ACCOUNT=$(cat config.json | jq -r '.gcloud_compute_service_account')
if [ $? -gt 0 ]; then
  echo "Unable to find 'gcloud_compute_service_account' in config.json"
  exit 1
fi

for f in $functions; do 
    gcloud functions deploy $f --timeout=120 --entry-point $f --runtime python37 --trigger-http --source=./ --service-account=$SERVICE_ACCOUNT
    if [ $? -gt 0 ]; then
        exit 1
    fi
done

exit 0
