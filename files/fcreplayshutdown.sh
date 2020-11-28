#!/bin/bash
# This is called when a shutdown event is run
cd /home/fcrecorder/fcreplay
source ./venv/bin/activate
fcreplaydestroy destroy
sleep 5