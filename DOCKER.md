Run with

docker run -it \
  --rm \
  --cpus=4 \
  -v <.ia_FILE>:/root/.ia:ro \
  -v <.youtube-upload-credentials.json>:/root/.youtube-upload-credentials.json:ro \
  -v <.client_secrets.json>:/root/.client_secrets.json:ro \
  -v <description_append.txt>:/root/description_append.txt:ro \
  -v <config_FILE>:/root/config.json:ro \
  -v <Fightcade_PATH>:/Fightcade:ro \
  -v <AVI_PATH>:/Fightcade/emulator/fbneo/avi \
  -v `mktemp -d`:/Fightcade/emulator/fbneo/fightcade \
  -p 5900:5900 \
  fcreplay:latest
