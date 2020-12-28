FROM python:3.8-buster

LABEL maintainer="glisignoli"

# Required packages for build/run
RUN apt-get update && apt-get install -y \
  bash \
  ffmpeg \
  fontconfig \
  git \
  i3 \
  i3status \
  mencoder \
  pulseaudio \
  software-properties-common \
  wget \
  x11vnc \
  xterm \
  xvfb \
  zenity \
  zlib1g-dev

RUN apt-add-repository contrib && \
  apt-add-repository non-free

RUN dpkg --add-architecture i386 && \
  apt update && \
  apt install -y \
    wine \
    wine32 \
    wine64 \
    libwine \
    libwine:i386 \
    fonts-wine \
    winetricks

RUN pip3 install --upgrade cython pip scikit-build

# Fix wine sound and video recording
RUN winetricks -q avifil32 && \
  winetricks -q d3dx9 && \
  winetricks sound=pulse

# Download Fightcade linux
RUN cd / && \
  wget https://www.fightcade.com/download/linux && \
  tar xvf linux && \
  mkdir -p /Fightcade/emulator/fbneo/config && \
  mkdir -p /Fightcade/emulator/fbneo/ROMs && \
  rm -rf /linux

# Download and install youtube-dl
RUN cd /root && \
  pip install --upgrade google-api-python-client oauth2client progressbar2 && \
  git clone https://github.com/tokland/youtube-upload.git && \
  cd youtube-upload && \
  python3 setup.py install

# Install fcreplay
COPY fcreplay /root/fcreplay
COPY setup.py /root/setup.py
RUN cd /root && python3 setup.py install

# Setup i3 for autostart
RUN mkdir -p /root/.config/i3
COPY files/i3_config /root/.config/i3/config
COPY files/startup.sh /root/i3_startup.sh
RUN chmod 0755 /root/i3_startup.sh

# Create Xauthroity and empty log file
RUN touch /root/.Xauthority && touch /root/fcreplay.log

# Disable pulseaudio auto suspend
COPY files/default.pa /etc/pulse/default.pa
COPY files/system.pa /etc/pulse/system.pa

# Copy over configuration files for xaudio fix
COPY files/fcadefbneo.default.ini /Fightcade/emulator/fbneo/config/fcadefbneo.default.ini
COPY files/fcadefbneo.ini /Fightcade/emulator/fbneo/config/fcadefbneo.ini

COPY files/docker-entrypoint.sh /docker-entrypoint.sh

CMD ["fcrecord"]
ENTRYPOINT ["/docker-entrypoint.sh"]
