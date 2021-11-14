#!/bin/bash
# Check if the first argument is '--debug'
if [ "$1" = "--debug" ]; then
  docker-compose run -p 80:80 -p 5678:5678 \
    -e FLASK_APP=fcreplay.site.app:app \
    --workdir=/app/ \
    --entrypoint python \
    fcreplay-site -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m flask run -h 0.0.0.0 -p 80
else
  docker-compose run -p 80:80 -p 5678:5678 -e FLASK_ENV=development fcreplay-site
fi
