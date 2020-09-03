#!/bin/bash
# Get service account and project
SERVICE_ACCOUNT=$(cat config.json | jq -r '.gcloud_compute_service_account')
if [ $? -gt 0 ]; then
  echo "Unable to find 'gcloud_compute_service_account' in config.json"
  exit 1
fi

PROJECT=$(cat config.json | jq -r '.gcloud_project')
if [ $? -gt 0 ]; then
  echo "Unable to find 'gcloud_project' in config.json"
  exit 1
fi

gcloud scheduler jobs create http 'check-for-replay' --schedule='*/2 * * * *' \
  --uri="https://us-central1-${PROJECT}.cloudfunctions.net/check_for_replay" \
  --oidc-service-account-email="$SERVICE_ACCOUNT" \
  --oidc-token-audience="https://us-central1-${PROJECT}.cloudfunctions.net/check_for_replay"

gcloud scheduler jobs create http 'video-status-update' --schedule='*/10 * * * *' \
  --uri="https://us-central1-${PROJECT}.cloudfunctions.net/video_status" \
  --oidc-service-account-email="$SERVICE_ACCOUNT" \
  --oidc-token-audience="https://us-central1-${PROJECT}.cloudfunctions.net/video_status"

exit 0
