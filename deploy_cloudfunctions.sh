#!/bin/bash
if [ $# -eq 0 ]; then
  functions="check_for_replay destroy_fcreplay_instance video_status check_environment get_top_weekly"
else
  functions=$1
fi

# Get service account
SERVICE_ACCOUNT=$(cat config.json | jq -r '.gcloud_compute_service_account')
if [ $? -gt 0 ]; then
  echo "Unable to find 'gcloud_compute_service_account' in config.json"
  exit 1
fi

for f in $functions; do 
    gcloud functions deploy $f --timeout=120 --entry-point $f --runtime python37 --trigger-http --service-account=$SERVICE_ACCOUNT
    if [ $? -gt 0 ]; then
        exit 1
    fi
done

exit 0