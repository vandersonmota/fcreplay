#!/bin/bash
# Depending on the hostname we want to do different things.
# Obviously this isn't the best solutions, but should work fine.
# This file needs to put in /usr/local/bin, owned by fbarecorder

# Do recording
if [[ "$HOSTNAME" == 'fcreplay-image-1' ]]; then
    startx
fi

# Do post processing
if [[ "$HOSTNAME" == 'fcreplay-postprocessing-1' ]]; then
    cd ~/fcreplay
    source ./venv/bin/activate
    fcreplaycloudpost
fi

exit 0