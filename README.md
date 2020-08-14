<!--ts-->
   * [About](#about)
   * [Goal](#goal)
      * [How it works](#how-it-works)
      * [Character Detection](#character-detection)
         * [A few more notes:](#a-few-more-notes)
      * [Todo](#todo)
      * [Requirements](#requirements)
         * [Uploading to youtube.com](#uploading-to-youtubecom)
         * [Uploading to archive.org](#uploading-to-archiveorg)
   * [Installation and setup](#installation-and-setup)
      * [Configuration](#configuration)
         * [Infrastructure Deployment](#infrastructure-deployment)
      * [Deployment](#deployment)
      * [Post Deployment Setup](#post-deployment-setup)
         * [Google cloud](#google-cloud)
   * [Usage](#usage)
      * [Activating](#activating)
      * [Getting replays](#getting-replays)
      * [Recording a replay](#recording-a-replay)
      * [Running automatically on startup](#running-automatically-on-startup)
      * [Google cloud](#google-cloud-1)

<!-- Added by: gino, at: Fri 14 Aug 2020 09:58:32 PM NZST -->

<!--te-->

# About
This project will upload encoded [fightcade](https://www.fightcade.com/) replays to archive.org: [Gino Lisignoli - Archive.org](https://archive.org/search.php?query=creator%3A%22Gino+Lisignoli%22)

A site the view the replays is here: https://fightcadevids.com

# Goal
The goal of this is to make fightcade replays accessible to anyone to watch without the need of using an emulator.

## How it works
fcreplaygetreplay will parse fightcade replay urls, then use the fightcade api details to create a encoding job and store it in a database.

fcreplayloop can then be used to record a replay:
1. Fightcade is started with wine
2. OBS is started to record the match
3. Match is finished
4. OBS is killed the python script takes over again.

The script then:
 1. Renames the file to the fightcade id
 2. Runs ffmpeg to correct it since killing OBS might break the file
 3. Runs ffmpeg again to generate a thumbnail
 4. Tries to determine which characters players are using OpenCV
 5. Uploads the file to archive.org with the relevant metadata
 6. Uploads the file to youtube.com with the relevant metadata 
 7. Removes the generated files.

## Character Detection
OpenCV is used to analise the video and match character names from the health bars. It does this by template matching the included character name images against the video every 60 frames. Depending on your OBS recording settings you might need to regenerate the images.

Currently this is only supported for 3rd strike.

### A few more notes:
To trigger OBS the screen is captured, looking for a the split windows and then checking for differences in the screen capture. Without memory inspection it doesn't seem like there is a way to tell when the emulator has started playing the replay.

Because fightcade doesn't have the ability to record to a video file you need to use some sort of capture software.

For this project [Open Broadcaster Software](https://obsproject.com/) is used to encode the video.

The i3 window manager is used to ensure that the fcadefbneo window is always in the same place, and have preconfigured OBS to record that area.

This is all done in a headless X11 session

## Todo
 - Better exception handling.
 - Better capturing of OBS and Wine output.
 - Support for games other than 3rd strike.
 - Find something that might be more lightweight than OBS.
   - ffmpeg with x11 capturing was attempted, but the framerate was unacceptible
 - Thumbnails are generated but not used

## Requirements
To run this, you need:
 1. A VM or physical machine.
     1. With at least 4 Cores (Fast ones would be ideal)
     1. With at least 4GB Ram
     1. With at least 30GB of storage 
 1. Running Fedora 32 (you can probably make this work in other distributions as well)
     1. You really want to use a minimal installation
 1. Some familiarity with linux will help

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
3. Create the base instance from the fedora32 image
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
I've include a basic ansible playbook for the installation, you will need to have ssh access and a deployment user with root access.

2. Use the ansible script to setup the base instance.
   1. Create a deployment user with with sudo access: `adduser deployment`
   2. Set a password `passwd deployment`
   3. Add the user to the wheel group: `groupmems -a deployment -g wheel`
   4. Copy your ssh key with `ssh-copy-id deployment@<host>`
   5. Disable password login in the `/etc/ssh/sshd_config` and restart sshd: `systemctl restart sshd`
   6. `ansible-playbook -i <host>, -u <deployment_user> -K --diff --extra-vars '{"gcloud": True, "FC2_PATH": "/path/to/local/FC2" }' playbook.yml`
 
## Post Deployment Setup
Login and switch to the fcrecorder user, then create a x11vnc password as the fcrecorder user (It will be stored in ~/.vnc/passwd):
```commandline
x11vnc -storepasswd 
```

Now you need to start the dummy X server, configure fightcade and configure OBS.
As the fcrecorder user:
```commandline
# Run tmux, and split so you have two panes
# In the first pane, run startx
startx
# In the second pane, run x11vnc
x11vnc --rfbauth ~/.vnc/passwd -noxfixes -noxdamage -noxrecord
```

### Google cloud
When deploying with the ansible playbook, and `"gcloud": True`, the fcrecord service is automaticall set to start when the hostname is fcreplay-image-1

This will cause `fcreplayloop --gcloud` to be automatically run when the instance is started.

# Usage

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
Once you have setup the base image, you need to make a image called: fcreplay-image:
```commandline
gcloud compute images create fcreplay-image \
  --source-disk fcrecorder\
  --source-disk-zone us-central1-a \
  --family fedora32 \
  --storage-location us-central1
```

Once you have created a image, you should create a scheduled job to check for replays to encode. Once a replay to encode has been found, the scheduler will call the google cloud function `check_for_fcreplay`. This will look for a replay in the database with the status 'ADDED'. It will then launch compute engine instance called `fcreplay-image-1` from the `fcreplay-image` instance.

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