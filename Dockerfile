FROM i386/alpine:3

LABEL maintainer="glisignoli"

# Required packages for build/run
RUN apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/testing \
  bash \
  cmake \
  ffmpeg \
  fontconfig \
  g++ \
  gcc \
  git \
  i3status \
  i3wm \
  jpeg \
  jpeg-dev \
  lcms2-dev \
  libffi-dev \
  libjpeg \
  libjpeg-turbo-dev \
  libxslt-dev \
  linux-headers \
  make \
  msttcorefonts-installer \
  musl \
  musl-dev \
  openjpeg \
  openjpeg-dev \
  openjpeg-tools \
  postgresql-dev \
  pulseaudio \
  python3 \
  python3-dev \
  python3-tkinter \
  py3-pip \
  py3-setuptools \
  wine \
  winetricks \
  x11vnc \
  xterm \
  xvfb \
  zenity \
  zlib-dev
RUN pip3 install --upgrade cython pip scikit-build

# Fix wine sound and video recording
RUN winetricks -q avifil32 && \
  winetricks -q d3dx9 && \
  winetricks sound=pulse

# Fix i3 Fonts
RUN update-ms-fonts

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

CMD ["record"]
ENTRYPOINT ["/docker-entrypoint.sh"]
