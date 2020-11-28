#!/bin/bash
NEWHOSTNAME=`cat /var/lib/cloud/data/set-hostname | grep hostname | awk '{print $2}' | sed 's/\"//g'`
echo $NEWHOSTNAME > /etc/hostname
hostname $NEWHOSTNAME