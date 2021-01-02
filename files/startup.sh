#!/bin/bash
cd /root

# Needed to initalise i3 sockets
export I3SOCK=$(i3 --get-socketpath)

# Needed to resolve a bug that is in pyperclib (used by cmd2)
# See: https://github.com/asweigart/pyperclip/issues/141 
export XDG_SESSION_TYPE=x11

# This sleep is needed so that the fcreplay-tasker container can attach
# the extra networks needed for fcreplay to work
sleep 2

fcreplay instance

# And these sleeps? I *think* they are needed for the python-loki-logging
# module, so that it reads the file before the container is closed too quickly
sleep 1
echo '' >> /root/fcreplay.log
sleep 1

pkill -9 tail
pkill -9 i3
pkill -9 xterm
pkill -9 x11vnc
pkill -9 Xvfb