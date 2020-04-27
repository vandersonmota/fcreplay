#!/bin/bash
URL=$1
FCREPLAY_DIR=`cat config.json|jq .fcreplay_dir -M -r`
GGPO_DIR=`cat config.json|jq .pyqtggpo_dir -M -r`
LOGFILE=`cat config.json|jq .logfile -M -r`

let TIME=${2}-3
cd $GGPO_DIR
./ggpofba.sh "$1" &

# If the sound is less than 10 (silent) for 30 seconds, stop recording
soundmeter --trigger -10 30 --segment 1 --action exec-stop --exec $FCREPLAY_DIR/stoprecord.sh --daemonize

# If sound starts playing then continue
soundmeter --trigger +1000 --action stop

# Kill failsafe soundmeter in case game is quiet
pkill -9 soundmeter

# Check if ggpo is actually running or crashed. If it isn't running, update script and exit
if ! pgrep ggpo > /dev/null; then
  echo "ERROR: GGPO isn't running! Crashed?" >> ${LOGFILE}
  echo fail > ${FCREPLAY_DIR}/tmp/status
fi

# Start pre-configured OBS
timeout $TIME obs --minimize-to-tray --startrecording || pkill -9 ggpofba

# Set fcreplay to pass
echo pass > ${FCREPLAY_DIR}/tmp/status
