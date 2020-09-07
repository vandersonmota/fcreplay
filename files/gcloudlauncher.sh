#!/bin/bash
# Depending on the hostname we want to do different things.
# Obviously this isn't the best solutions, but should work fine.
# This file needs to put in /usr/local/bin, owned by fcrecorder

# Sometimes this this files is run before the network is working. Which causes fcreplay to not start.
# Easiest way to fix this is to wait until we get a successful metadata request:
while true; do 
    service_name=$(curl http://metadata.google.internal/computeMetadata/v1/instance/name --header 'Metadata-Flavor: Google')
    if [ $? -eq 0 ]; then
        break
    fi
done

echo "Service name found as: ${service_name}" | logger
echo "Service name found as: ${service_name}"

# Do recording
if [[ $service_name =~ 'fcreplay-image-' ]]; then
    logger "restarting google-fluentd"
    sudo /usr/bin/systemctl restart google-fluentd
    logger "Starting recording Xorg as `whoami`"
    startx
fi

exit 0
