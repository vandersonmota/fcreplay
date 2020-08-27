# Development notes
<!--ts-->
   * [Development notes](#development-notes)
      * [Remote debuging](#remote-debuging)
      * [Database](#database)
      * [Processing order:](#processing-order)
      * [Processing tracking](#processing-tracking)
         * [Job status definitions](#job-status-definitions)

<!-- Added by: gino, at: Thu 27 Aug 2020 10:23:29 PM NZST -->

<!--te-->

## Remote debuging
You can enable remote debuging by setting the environment variable `REMOTE_DEBUG=true` then connect to your remote instance on port 5678. To disable remote debuging you need to unset the environment variable.

The following vscode example launch configuration will allow you connect to the remote instance:
```json
{
  "name": "FCReplay HyperV",
  "type": "python",
  "request": "attach",
  "justMyCode": false,
  "connect": {
    "host": "192.168.1.88",
    "port": 5678
  },
  "pathMappings": [
    {
      "localRoot": "/home/user/git/fcreplay/fcreplay",
      "remoteRoot": "/home/fcrecorder/fcreplay/venv/lib/python3.8/site-packages/fcreplay-0.9-py3.8.egg/fcreplay"
    }
  ]
}
```

## Database
The database is defined in `models.py`. Tested on postgresql
Interacting with the database should be done through the database class.
```python
from fcreplaydatabase import Database
db = Database()
```

## Processing order:
Processing a replay involves many steps. To start with, look at the `main` function of loop.py

## Processing tracking
The database table `job` contains a list of running jobs. Once a job has been finished it is removed from the `job` table. The status of the job can be retrieved from `replay.status` 

### Job status definitions
|status|definition|
|-|-|
|JOB_ADDED|Processing job added, awaiting processing|
|RECORDING|Launching Emulator and OBS|
|RECORDED|replay.mkv created by obs successfuly|
|MOVED|replay.mkv moved to `./finished/dirty_{replay.id}.mkv`|
|DESCRIPTION_CREATED| Description was created |
|BROKEN_CHECK| File was run though ffmpeg to fix a 'dirty' close |
|THUMBNAIL_CREATED| Thumbnail file was successfuly created |
|UPLOADED_TO_IA| File was successfuly uploaded to archive.org
|UPLOADED_TO_YOUTUBE| File was successfuly uploaded to youtube |
|REMOVED_GENERATED_FILES| Generated files were removed |
|FINISHED| Replay was processed successfuly |
|FAILED|An unhandled exception was generated |