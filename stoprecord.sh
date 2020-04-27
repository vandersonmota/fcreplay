#!/bin/bash
FCREPLAY_DIR=`cat config.json|jq .fcreplay_dir -M -r`
pkill -9 capture
pkill -9 obs
pkill -9 fba
echo failed > ${FCREPLAY_DIR}/status
