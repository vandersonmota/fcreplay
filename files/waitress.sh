#!/bin/bash
cd /app/
waitress-serve --port=80 'fcreplay.site.app:app'
