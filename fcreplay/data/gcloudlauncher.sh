#!/bin/bash
# Depending on the hostname we want to do different things.
# Obviously this isn't the best solutions, but should work fine.

# Do recording
if [ $HOSTNAME -eq 'fcreplay-image-1' ]; then
    startx
fi

# Do post processing
if [ $HOSTANME -eq 'fcreplay-postprocessing-1' ]; then
    cd ~/fcreplay
    source ./venv/bin/activate
    fcreplaycloudpost
fi