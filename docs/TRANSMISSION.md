## Transmission

There is no need to edit Transmission's settings in `transmission-settings.json` unless you want more fine-grained control.
If you're making changes be sure to follow the [official settings](https://github.com/transmission/transmission/wiki/Editing-Configuration-Files).

The username and password default to `admin` / `admin` and are populated from the variables `TRANSMISSION_USER` and `TRANSMISSION_PASS` in the `.env` file.

**NOTE**: Do not change the values `download-dir` and `incomplete-dir` as they're internal to transmission's container and won't do what you think it may be doing.

**NOTE**: If you make any changes to `transmission-settings.json` you'll have to recreate the transmission container for the changes to take place:

    docker-compose up -d --force-recreate transmission
    
