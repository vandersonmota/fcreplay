# Cloud deployment
To deploy to google cloud you need to:

1. Create a project
2. Create a fedora32 image
4. Download the project api key as ~/.fcrecorder-api-credentials.json
3. Have gcloud command line installed and your project/region set
5. Run terraform script
6. Disable the google cloud scheduled job

## Configure base image
1. After running the terraform script ssh onto the fcrecorder machine. This is the image recording instances are provisioned from
   1. Confirm that the root partition has actually resized, mine didn't
2. Use the ansible script to setup the image.
   1. Create a deployment user with with sudo access
   2. Copy your ssh key with `ssh-copy-id deployment@<host>`
   3. Disable password login in the `/etc/ssh/sshd_config` and restart sshd: `systemctl restart sshd`
   4. `ansible-playbook -i <host>, -u <deployment_user> --diff --extra-vars '{"gcloud": True}' playbook.yml`
   
## Configure OBS and FightCade
Once ansible has setup the base image, you need to setup OBS and FightCade.

1. SSH onto the image
2. Switch to the fcrecorder user
3. Start a Tmux session
4. In one Tmux pane, run `startx`
5. In another Tmux pane, rune: `x11vnc -storepasswd ` to set a vnc password
6. Then run: `x11vnc -storepasswd `

Using a vnc client, connect to the fcrecorder instance and configure OBS and FightCade