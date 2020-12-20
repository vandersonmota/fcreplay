#!/bin/bash
cd /root
fcreplay instance 
sleep 1
echo '' >> /root/fcreplay.log
sleep 1

pkill -9 tail
pkill -9 i3
pkill -9 xterm
pkill -9 x11vnc
pkill -9 Xvfb