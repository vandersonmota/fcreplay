#!/bin/bash
# Look for arguments
function help() {
    echo "No argument supplied. Use one of 'fcrecord', 'fcreplayget', 'tasker', or 'validate'"
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

function fcreplayvalidate() {
    cd /root
    /usr/bin/fcreplayvalidate $@
}

function fcreplayget() {
    cd /root
    /usr/bin/fcreplayget $@
}

function fctasker() {
    cd /root
    /usr/bin/fcreplaytasker $@
}

if [ $# -eq 0 ]; then
    help
fi

# Look for the first argument
case $1 in
  fcrecord)
    fcrecord ${@:2}
    ;;

  fcreplayget)
    fcreplayget ${@:2}
    ;;
  
  tasker)
    fctasker ${@:2}
    ;;

  validate)
    fcvalidate ${@:2}
    ;;

  *)
    help 
    ;;
esac
