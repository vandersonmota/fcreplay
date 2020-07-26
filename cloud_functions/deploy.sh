#!/bin/bash
functions="check_for_replay check_for_postprocessing destroy_fcreplay destroy_fcreplay_postprocessing" 
for f in $functions; do 
    gcloud functions deploy $f --entry-point $f --runtime python37 --trigger-http --source=./ &
done