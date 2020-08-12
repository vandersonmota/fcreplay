#!/bin/bash

# Get config
cp ../config.json ./

# Get service account
SERVICE_ACCOUNT=$(cat config.json | jq -r '.gcloud_compute_service_account')
if [ $? -gt 0 ]; then
  echo "Unable to find 'gcloud_compute_service_account' in config.json"
  exit 1
fi

gcloud scheduler jobs create http 'check-for-replay' --schedule='*/2 * * * *' \
  --uri="https://us-central1-fcrecorder-286007.cloudfunctions.net/check_for_replay" \
  --oidc-service-account-email="$SERVICE_ACCOUNT" \
  --oidc-token-audience="https://us-central1-fcrecorder-286007.cloudfunctions.net/check_for_replay"

exit 0
