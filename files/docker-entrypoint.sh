#!/bin/bash
# Look for arguments
function help() {
    echo "No argument supplied. Use one of 'fcrecord', 'fcreplay'"
    exit 1
}

function fcrecord() {
    Xvfb -screen :0 1024x768x16 > /dev/null 2>&1 &
    sleep 1
    export DISPLAY=:0
    export WINEDEBUG=-all
    i3 > /dev/null 2>&1 &
    tail -f /root/fcreplay.log
}

function fcreplay() {
    cd /root
    /usr/bin/fcreplay $@
}

if [ $# -eq 0 ]; then
    help
fi

# Look for the first argument
case $1 in
  fcrecord)
    fcrecord ${@:2}
    ;;

  fcreplay)
    fcreplay ${@:2}
    ;;
  
  *)
    help 
    ;;
esac
