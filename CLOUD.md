# Cloud deployment
To deploy to google cloud you need to:

1. Create a project
2. Create a fedora32 image
4. Download the project api key as ~/.fcrecorder-api-credentials.json
3. Have gcloud command line installed and your project/region set
5. Run terraform script

## Creating base image
1. Create a Google Cloude Engine instance from the 'fedora-32' image called 'fcrecorder'
   1. This machine will be powered off most of the time, so the requirements don't matter. This machine will contain the fcreplay code used to record and upload fightcade replays
   2. Deploy it with a 20gb Disk. Power it on and confirm that the root partition has actually resized
2. Use the ansible script to setup the image.
   1. Create a deployment user with with sudo access
   2. Copy ssh key with `ssh-copy-id deployment@<host>`
   3. `ansible-playbook -i <host>, -u <deployment_user> --diff --extra-vars '{"gcloud": True}' playbook.yml`