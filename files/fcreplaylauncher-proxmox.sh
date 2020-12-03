#!/bin/bash
# Depending on the hostname we want to do different things.
# Obviously this isn't the best solutions, but should work fine.
# This file needs to put in /usr/local/bin, owned by fcrecorder

service_name=`cat /etc/hostname`

echo "Service name found as: ${service_name}" | logger
echo "Service name found as: ${service_name}"

# Do recording
if [[ $service_name =~ 'fcreplay-image-' ]]; then
    logger "Starting recording Xorg as `whoami`"
    startx
fi

exit 0