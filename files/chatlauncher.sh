#!/bin/bash
cd /home/fcrecorder/fightcadechat
source ./venv/bin/activate
while true; do timeout 1h fightcadechat; done