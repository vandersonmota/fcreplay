#!/bin/bash
# This script will check deployment files are present and then deploy
# fcreplay with ansible

WARN=0
ERROR=0

# Warn if optional files are not present:
declare -a warn_files
warn_files+=('description_append.txt')
warn_files+=('.youtube-upload-credentials.json')
warn_files+=('.client_secrets.json')
warn_files+=('.ia')

for f in "${warn_files[@]}"; do
    if [ ! -f $f ]; then
        echo "WARNING: Optional file '${f}' not found"
        WARN=1
    else
        echo "PASS:    Optional file '${f}' found"
    fi
done

# Check for autostart
if [ ! -z $FCREPLAY_AUTOSTART ]; then
    if [[ $FCREPLAY_AUTOSTART == true || $FCREPLAY_AUTOSTART == false ]]; then
        echo "PASS:    Optional environment variable FCREPLAY_AUTOSTART (${FCREPLAY_AUTOSTART}) is set"
    else
        echo "ERROR:   Optional environment variable FCREPLAY_AUTOSTART (${FCREPLAY_AUTOSTART}) is not true or false"
        ERROR=1
    fi
else
    echo "ERROR: Environment variable 'FCREPLAY_AUTOSTART' is not set"
    ERROR=1
fi

# Check for proxmox
if [ ! -z $FCREPLAY_PROXMOX ]; then
    if [[ $FCREPLAY_PROXMOX == true || $FCREPLAY_PROXMOX == false ]]; then
        echo "PASS:    Optional environment variable FCREPLAY_PROXMOX (${FCREPLAY_PROXMOX}) is set"
    else
        echo "ERROR:   Optional environment variable FCREPLAY_PROXMOX (${FCREPLAY_PROXMOX}) is not true or false"
        ERROR=1
    fi
else
    echo "ERROR: Environment variable 'FCREPLAY_PROXMOX' is not set"
    ERROR=1
fi

# Check for FC2_PATH environment variable
if [ ! -z $FC2_PATH ]; then
    if [ ! -d $FC2_PATH ]; then
        echo "WARNING:   Optional environment variable FC2_PATH (${FC2_PATH}) is not a directory"
        WARN=1
    else
        echo "PASS:    Optional environment variable FC2_PATH (${FC2_PATH}) is a directory"
    fi
else
    echo "WARNING: Optional environment variable 'FC2_PATH' is not set"
    WARN=1
fi

# Check for FCREPLAY_CONFIG environment variable
if [ ! -z $FCREPLAY_CONFIG ]; then
    if [ ! -f $FCREPLAY_CONFIG ]; then
        echo "WARNING: Optional environment variable FCREPLAY_CONFIG (${FCREPLAY_CONFIG}) is not a file"
        WARN=1
    else
        echo "PASS:    Optional environment variable FCREPLAY_CONFIG (${FCREPLAY_CONFIG}) is a file"
    fi
else
    echo "WARNING: Optional Environment variable 'FCREPLAY_CONFIG' is not set"
    WARN=1
fi

# Check for FCREPLAY_BRANCH environment variable
if [ ! -z $FCREPLAY_BRANCH ]; then
    echo "PASS:    Required environment variable FCREPLAY_BRANCH (${FCREPLAY_BRANCH}) is set"
else
    echo "ERROR:   Required environment variable 'FCREPLAY_BRANCH' is not set"
    ERROR=1
fi

# Check for FCREPLAY_GCLOUD environment variable
if [ ! -z $FCREPLAY_GCLOUD ]; then
    if [[ $FCREPLAY_GCLOUD == true || $FCREPLAY_GCLOUD == false ]]; then
        echo "PASS:    Optional environment variable FCREPLAY_GCLOUD (${FCREPLAY_GCLOUD}) is set"
    else
        echo "ERROR:   Optional environment variable FCREPLAY_GCLOUD (${FCREPLAY_GCLOUD}) is not true or false"
        ERROR=1
    fi
else
    echo "WARNING: Optional environment variable 'FCREPLAY_GCLOUD' is not set"
    WARN=1
fi


if [ $ERROR -gt 0 ]; then exit 1; fi
if [ $WARN -gt 0 ]; then exit 1; fi

echo "You can run ansible with: 'ansible-playbook -i <host>, -u <deployment_user> -K --diff playbook.yml"
