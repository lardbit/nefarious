# nefarious

[![Build Status](https://travis-ci.org/lardbit/nefarious.svg?branch=master)](https://travis-ci.org/lardbit/nefarious)
[![Docker Pulls](https://img.shields.io/docker/pulls/lardbit/nefarious.svg?maxAge=60&style=flat-square)](https://hub.docker.com/r/lardbit/nefarious)

**nefarious is a web application that helps you download Movies and TV Shows.**

It aims to combine features of [Sonarr](https://github.com/Sonarr/Sonarr/), [Radarr](https://github.com/Radarr/Radarr) and [Ombi](https://github.com/tidusjar/Ombi).

It uses [Jackett](https://github.com/Jackett/Jackett/) and [Transmission](https://transmissionbt.com/) under the hood.  Jackett searches for torrents and Transmission does the downloading.

Features:
- [x] Search TV & Movies
- [x] Auto download TV (individual episodes or full season)
- [x] Auto download Movies
- [x] Discover TV & Movies (by popularity, genres, year etc)
- [x] Find similar TV & Movies
- [x] Find recommended TV & Movies
- [x] Manually search jackett's torrent results and download
- [x] Supports blacklisting torrent results (i.e avoid a bad/fake torrent that should be avoided)
- [X] Supports quality profiles (i.e only download *1080p* Movies and *any* quality TV)
- [x] Supports whether to download media with hardcoded subtitles or not
- [x] Supports user defined keywords to filter results (i.e ignore "x265", "hevc" codecs)
- [x] Auto download TV & Movies once it's released (routinely scan)
- [x] Monitor transmission results & status from within the app
- [x] Self/auto updating application
- [x] Supports multiple users and permission groups (i.e admin users and regular users)
- [x] Responsive Design (looks great on desktops, tablets and small devices like phones)
- [x] Movie trailers
- [x] Automatically renames media
- [x] Supports multiple languages (TMDB supports internationalized Titles, Descriptions and Poster artwork)
- [ ] Support user requests (i.e an unprivileged user must "request" to watch something)

### Contents

- [Installing](#installing)
- [Running](#running)
- [Demo](#demo)
- [Screenshots](#screenshots)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

### Demo

![](screenshots/nefarious-demo.gif)

### Screenshots

#### Login
![](screenshots/login.png)
#### Search
![](screenshots/search-results.png)
#### TV Result
![](screenshots/media-tv-result.png)
#### Movie Result
![](screenshots/media-movie-result.png)
#### Movie Custom Quality Profile
![](screenshots/media-movie-custom-quality-profile.png)
#### Download Status
![](screenshots/media-status.png)
#### Discover
![](screenshots/discover.png)
#### Wanted
![](screenshots/wanted.png)
#### Watching
![](screenshots/watching.png)
#### Settings
![](screenshots/settings.png)
#### Search Manual
![](screenshots/search-manual.png)
#### Mobile Friendly
![](screenshots/search-mobile.png)


### Installing

nefarious is best run via [Docker](https://hub.docker.com/search/?type=edition&offering=community) through [Docker Compose](https://docs.docker.com/compose/install/).

Install that and you're all set.

### Running

Run nefarious and dependencies:
    
    docker-compose up -d
    
nefarious and all dependencies are now running.  See below for configuration details.

**NOTE:** There is an *ARM* compatible version (`docker-compose.arm.yml`) as well which allows you to run nefarious on hardware like the raspberry pi, odroid etc.

Run nefarious on ARM architectures:
    
    docker-compose -f docker-compose.arm.yml up -d
    
You'll always have to include `-f docker-compose.arm.yml` in the command unless you rename the file to `docker-compose.yml`.

#### Configure Jackett

Configure your local Jackett instance at [http://localhost:9117](http://localhost:9117).  You'll need to add indexers and copy your api key to enter into nefarious.  Some popular examples are *The Pirate Bay*, *1337x*, *RARBG*.

#### Configure Transmission

The default download path is `/tmp/transmission`, so make sure to edit the `docker-compose.yml` to change that to something like:
  
    /home/bob/Downloads:/downloads
    
Where the new download path would be `/home/bob/Downloads`.  Leave the right side alone, i.e `/downloads` as that maps to an internal container path.

**Windows** users: use forward slashes in your download path despite your hesitation, i.e  `c:/users/bob/downloads:/downloads`.

After editing anything in `docker-compose.yml`, you'll need to restart the containers by running:

    docker-compose up -d

There is no default transmission user/pass, but feel free to edit the `transmission-settings.json` beforehand following the [official settings](https://github.com/transmission/transmission/wiki/Editing-Configuration-Files) to make any changes you'd like.

**NOTE** if you make any changes to `transmission-settings.json` you'll have to recreate the transmission container for the changes to take place:

    docker-compose up -d --force-recreate transmission

You can view transmission's web ui at [http://localhost:9091](http://localhost:9091) to see what's actually being downloaded by nefarious.

#### Configure nefarious
    
The default user/pass is `admin/admin`.  You can change this on settings page.

Open nefarious at [http://localhost:8000](http://localhost:8000).  You'll be redirected to the settings page.

###### Jackett settings

Since jackett is running in the same docker network, you'll need to set the host as `jackett`.  The default port is `9117`.  Enter your api token.

###### Transmission settings

Configure your transmission host, port, username and password, and download sub-directories.  nefarious will save TV and Movies in individual sub-folders of your configured Transmission download path.

If you're using the built-in transmission in the `docker-compose.yml`, then make sure to enter `transmission` as the host since it's in the same docker network stack.

There is no default transmission user/pass, so leave those blank if you didn't manually set those.

## Troubleshooting
   
    # logs for main app
    docker-compose logs -f nefarious

    # logs for tasks (search results)
    docker-compose logs -f celery

    # list all services (they should all be "up")
    docker-compose ps

    # use hammer and restart everything (you won't lose your settings, though)
    docker-compose down
    docker-compose up -d


## Development

If you're interested in contributing or simply want to run nefarious without *docker* then follow these instructions.

nefarious is built on:

- Python 3.6
- Django 2
- Angular 6
- Bootstrap 4

*Note*: Review the `Dockerfile` for all necessary dependencies.

#### Install python dependencies

This assumes you're either installing these packages in your global python environment (in which case you probably need to use `sudo`) or, even better, install a [virtual environment](https://docs.python.org/3/library/venv.html) first.
  
    pip install -r src/requirements.txt

#### Build database
  
    python src/manage.py migrate

#### Run nefarious init script

This creates a default user and pass (admin/admin).

    python src/manage.py nefarious-init admin admin@localhost admin


#### Build front-end resources

First install the frontend dependencies:

    npm --prefix src/frontend install

Then build the frontend html/css stuff (angular):
    
    npm --prefix src/frontend run build
   
Note: run `npm --prefix src/frontend run watch` to automatically rebuild while you're developing the frontend stuff.
   
#### Run nefarious

Run the python application using django's *development* `runserver` management command: 

    DEBUG=1 python src/manage.py runserver 8000
   
It'll be now running at [http://127.0.0.1:8000](http://127.0.0.1:8000)

   
#### Run celery (task queue)

[Celery](http://celeryproject.org) is a task queue and is used by nefarious to queue downloads, monitor for things, etc.

Run the celery server:

    cd src
    celery -A nefarious worker --loglevel=INFO
    
You'll see all download logs/activity come out of here.

#### Dependencies

Jackett, Redis and Transmission are expected to be running somewhere.  

You can download and run them manually, or, for simplicity, I'd just run them via docker using the `docker-compose.yml` file.

Run redis, jackett and transmission from the `docker-compose.yml` file:

    docker-compose up -d redis jackett transmission
