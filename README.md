<!--ts-->
   * [About](#about)
   * [Goal](#goal)
   * [Features](#features)
      * [Description generation](#description-generation)
   * [Requirements](#requirements)
      * [Database](#database)
      * [Optional: Google cloud](#optional-google-cloud)
         * [A few more notes:](#a-few-more-notes)
      * [Todo](#todo)
      * [Requirements](#requirements-1)
         * [Uploading to youtube.com](#uploading-to-youtubecom)
         * [Uploading to archive.org](#uploading-to-archiveorg)
   * [Installation and setup](#installation-and-setup)
      * [Configuration](#configuration)
         * [Infrastructure Deployment](#infrastructure-deployment)
      * [Deployment](#deployment)
      * [Monitoring Recording](#monitoring-recording)
         * [Google cloud](#google-cloud)
   * [Usage](#usage)
      * [Activating](#activating)
      * [Getting replays](#getting-replays)
      * [Recording a replay](#recording-a-replay)
      * [Running automatically on startup](#running-automatically-on-startup)
      * [Google cloud](#google-cloud-1)

<!-- Added by: gino, at: Tue 06 Oct 2020 09:28:14 PM NZDT -->

<!--te-->

# About
This project will automatically encoded [fightcade](https://www.fightcade.com/) replays and upload them to archive.org: [Gino Lisignoli - Archive.org](https://archive.org/search.php?query=creator%3A%22Gino+Lisignoli%22) or youtube: [fightcade archive](https://www.youtube.com/channel/UCrYudzO9Nceu6mVBnFN6haA)

A web site the view the archive.org replays is here: https://fightcadevids.com

fcreplay is primarly a python application used to automate the generation of fightcade replays as video files.

# Goal
The goal of this is to make fightcade replays accessible to anyone to watch without using an emulator.

# Features
fcreplay has several features to automate the encoding process and add aditional data to the generated videos

## Description generation
A desctiption is generated that contains:
1. The fightcade replay id
2. The fightcade player ids
3. The fightcade player locations
4. The game being played
5. The date the game was played
6. (Optional) A appended description

# Requirements
## Database
Fcreplay uses sqlalchemy and has been tested with postgres and is used store any replay metadata

## Optional: Google cloud
Fcreplay is designed to run on google cloud

### A few more notes:
To trigger recording the file `started.inf` is checked. If the file exists then pyautogui is used to start recording the avi file(s)

The i3 window manager is used to ensure that the fcadefbneo window is always in the same place.

This is all done in a headless X11 session

## Todo
 - Better exception handling.
 - Thumbnails are generated but not used

## Requirements
To run this, you need:
 1. A VM or physical machine.
     1. With at least 4 Cores (Fast ones would be ideal)
     1. With at least 4GB Ram
     1. With at least 250GB of storage 
        1. This is the amount of temporary storage required to encode a replay of up to 3 hours long. Replay recording requires ~20MB/sec
 2. Running Fedora 32
 3. Some familiarity with linux will help

### Uploading to youtube.com
To upload files to youtube.com you need to setup a youtube api endpoint. See here: https://github.com/tokland/youtube-upload

### Uploading to archive.org
To upload files to archive.org, set the configuration key `upload_to_ia` to `true` and configure the ia section in the configuration file. You will also need to have your `.ia` secrets file in your users home directory. This can be generated by running `ia configure` from the command line once you have setup the python virtual environment.

# Installation and setup
## Configuration
The defaults should work if you follow the guide below.

If you are using the ansible playbook, you will also want to have ready the following files:
 - Configuration file: `config.json`
 - Appened description: `description_append.txt`
 - Google cloud storage credentials: `.stroage_creds.json`
 - Google api client secrets: `.client_secrets.json`
 - Youtube upload credentials: `.youtube-upload-credentials.json`
 - Archive.org secrets: `.ia`


### Infrastructure Deployment
To deploy to google cloud you need to:

1. Create a project
2. Create a fedora32 image
   1. This was done by following: https://linuxhint.com/install-fedora-google-compute-engine
   2. Install google-fluentd
3. Create the base instance from the fedora32 image called fcreplay-image
4. Create a service account "fcrecorder-compute-admin"
   1. Give it the folowing roles:
      - Cloud Functions Invoker
      - Compute Admin
      - Logs Configuration Writer
      - Logs Writer
      - Monitoring Metric Writer
      - Service Account User
   2. Make add this in your config.json file
5. Deploy the cloud functions

## Deployment
I've include a basic ansible playbook for the installation, you will need to have ssh access to the `fcreplay-image` and a deployment user with root access.

2. Use the ansible script to setup the base instance.
   1. Create a deployment user with with sudo access: `adduser deployment`
   2. Set a password `passwd deployment`
   3. Add the user to the wheel group: `groupmems -a deployment -g wheel`
   4. Copy your ssh key with `ssh-copy-id deployment@<host>`
   5. Disable password login in the `/etc/ssh/sshd_config` and restart sshd: `systemctl restart sshd`
   6. Launch the ansible script:
      1. Development: `ansible-playbook -i <host>, -u <deployment_user> -K --diff --extra-vars '{"FC2_PATH": "/path/to/local/FC2", "gitbranch": "master" }' playbook.yml`
      2. Google Cloud: `ansible-playbook -i <host>, -u <deployment_user> -K --diff --extra-vars '{"gcloud": True, "FC2_PATH": "/path/to/local/FC2", "gitbranch": "master" }' playbook.yml`
      3. Google Cloud auto destroy: `ansible-playbook -i <host>, -u <deployment_user> -K --diff --extra-vars '{"destroy": True, "gcloud": True, "FC2_PATH": "/path/to/local/FC2", "gitbranch": "master" }' playbook.yml`
   7. After running the ansible script, you will need to start a xorg session and run `wine /home/fcrecorder/fcreplay/Fightcade/emulator/fbneo/fcadefbneo.exe` once to initialise wine
   8. Then run in a xorg session, run winetricks and install:
      * allcodecs
      * avifil32
      * cinepack
      * xvid
 
## Monitoring Recording
If you want to watch recording happening, you need to:
1. Login and switch to the fcrecorder user
2. Create a x11vnc password as the fcrecorder user `x11vnc -storepasswd`
3. Add a firewalld rule to allow connections `firewall-cmd '--add-port 5900/tcp`

When recording is happening, you can then run `x11vnc --rfbauth ~/.vnc/passwd -noxfixes -noxdamage -noxrecord` as the fcrecord user. This will start a vnc server allowing you to connect to your instance on port 5900


### Google cloud
When deploying with the ansible playbook, and the ansible variable `"gcloud": True`, the fcrecord service is automatically set to start when the hostname is fcreplay-image-1

This will cause `fcreplayloop --gcloud` to be automatically run when the instance is started. See `loop.py` for more info

# Usage
The typical useage of fcreplay is to run this in google cloud, where the service

## Activating
Before running fcreplay, you need to activate the python environment
```commandline
cd ~/fcreplay
source ./venv/bin/activate
```

## Getting replays
This will download a replay, and place it in the database
```commandline
fcreplayget <fightcade profile> <replay url>
```

## Recording a replay
Within a Xorg session:
```commandline
fcreplayloop
```
You can also run `fcreplayloop --debug` to only run for a single iteration. Useful for testing.

## Running automatically on startup
To run fcreplay automatically on startup you need to enable the service, and uncommet the i3 line:
```commandline
systemctl enable fcrecord
sed -i 's/^# exec "xterm/exec "xterm/' .config/i3/config
```

## Google cloud
Once you have setup the base image, you need to make a image called: fcrecord:
```commandline
gcloud compute images create fcreplay-image \
  --source-disk fcrecorder\
  --source-disk-zone us-central1-a \
  --family fedora32 \
  --storage-location us-central1
```


Once started, the instance will look for a replay on startup and begin encoding.

If you want to see the logs, the following query should work:

```
(logName="projects/fcrecorder/logs/fcreplay" AND labels."compute.googleapis.com/resource_name" = "fcreplay-image-1") OR
(resource.type="cloud_function" AND severity=INFO AND labels.execution_id:*)
```

To create a scheduled job, run:
```commandline
gcloud scheduler jobs create http 'check-for-replay' --schedule='*/2 * * * *' \
  --uri="https://us-central1-fcrecorder-286007.cloudfunctions.net/check_for_replay" \
  --oidc-service-account-email="fcrecorder-compute-account@fcrecorder-286007.iam.gserviceaccount.com" \
  --oidc-token-audience="https://us-central1-fcrecorder-286007.cloudfunctions.net/check_for_replay"
```