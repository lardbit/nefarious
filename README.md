# Nefarious

[![Build Status](https://travis-ci.org/lardbit/nefarious.svg?branch=master)](https://travis-ci.org/lardbit/nefarious)

**Nefarious is a web application that helps you download Movies and TV Shows.**

It aims to combine features of [Sonarr](https://github.com/Sonarr/Sonarr/), [Radarr](https://github.com/Radarr/Radarr) and [Ombi](https://github.com/tidusjar/Ombi).

It uses [Jackett](https://github.com/Jackett/Jackett/) under the hood and expects [Transmission](https://transmissionbt.com/) to be running somewhere.  It actually includes transmission but I suggest using [docker-transmission-openvpn](https://github.com/haugene/docker-transmission-openvpn) for a version built to run behind a VPN.

Features:
- [x] Search TV
- [x] Search Movies
- [x] Auto download TV (individual or full season)
- [x] Auto download Movies
- [x] Discover Movies (by popularity, genres etc)
- [x] Discover TV (by popularity, genres etc)
- [x] Manually search Jackett results and download
- [x] Support blacklisting torrent results
- [X] Support quality profiles (i.e only download 1080p Movies and *any* quality TV)
- [x] Auto download media once it's released (routinely scan)
- [x] Monitor transmission results from within the app
- [x] Self/auto updating application
- [x] Support multiple users (i.e admin users and regular users)
- [x] Mobile Friendly (looks good on small devices like phones)
- [ ] Support user requests (i.e a user must "request" to watch something)
- [ ] Smart Ratio management (auto seed to specified indexers)

### Contents

[Installing](#installing)

[Running](#running)

[Screenshots](#screenshots)

[Troubleshooting](#troubleshooting)

[Development](#development)

[Contributing](#contributing)

### Screenshots

##### Login
![](https://github.com/lardbit/nefarious/blob/master/screenshots/login.png?raw=true)
##### Search
![](https://github.com/lardbit/nefarious/blob/master/screenshots/search-blank.png?raw=true)
##### Search Results
![](https://github.com/lardbit/nefarious/blob/master/screenshots/search-results.png?raw=true)
##### TV Result
![](https://github.com/lardbit/nefarious/blob/master/screenshots/media-tv-result.png?raw=true)
##### Download Status
![](https://github.com/lardbit/nefarious/blob/master/screenshots/media-status.png?raw=true)
##### Movie Result
![](https://github.com/lardbit/nefarious/blob/master/screenshots/media-movie-result.png?raw=true)
##### Movie Custom Quality Profile
![](https://github.com/lardbit/nefarious/blob/master/screenshots/media-movie-custom-quality-profile.png?raw=true)
##### Discover
![](https://github.com/lardbit/nefarious/blob/master/screenshots/discover.png?raw=true)
##### Wanted
![](https://github.com/lardbit/nefarious/blob/master/screenshots/wanted.png?raw=true)
##### Watching
![](https://github.com/lardbit/nefarious/blob/master/screenshots/watching.png?raw=true)
##### Settings
![](https://github.com/lardbit/nefarious/blob/master/screenshots/settings.png?raw=true)
##### Search Manual
![](https://github.com/lardbit/nefarious/blob/master/screenshots/search-manual.png?raw=true)
##### Mobile Friendly
![](https://github.com/lardbit/nefarious/blob/master/screenshots/search-mobile.png?raw=true)


### Installing

Nefarious is best run via Docker through [Docker Compose](https://docs.docker.com/compose/install/).

Install that and you're all set.

### Running

Run nefarious and dependencies:
    
    docker-compose up -d

The default user/pass is `admin/admin`.  You can change this through the backend [admin interface](http://localhost:8000/admin/auth/user/1/password/).

**NOTE:** there is an [armv7 image](https://hub.docker.com/r/lardbit/nefarious/tags/) as well.

### Configure Jackett

Configure your local Jackett instance at [http://localhost:9117](http://localhost:9117).  You'll need to add indexers and copy your api key to enter into nefarious.

### Configure Transmission

If you're using the built-in transmission, then there's nothing to actually configure, but you can view its web ui at [http://localhost:9091](http://localhost:9091) to see what's actually being downloaded by nefarious.

### Configure Nefarious

Open nefarious at [http://localhost:8000](http://localhost:8000).  You'll be redirected to the settings page.

##### Jackett settings

Since jackett is running in the same docker network, you'll need to set the host as `jackett`.  The default port is `9117`.  Enter your api token.

##### Transmission settings

Configure your transmission host, port, username and password, and download directories.  Nefarious will save TV and Movies in individual sub-folders of your configured Transmission download path.

If you're using the built-in transmission in the `docker-compose.yml`, then make sure to enter `transmission` as the host since it's in the same docker network stack.

## Troubleshooting
   
    # logs for main app
    docker-compose logs -f nefarious

    # logs for tasks (search results)
    docker-compose logs -f celery


## Development

Nefarious is built on:

- Python 3.6
- Django 2
- Angular 6
- Bootstrap 4

Review the `Dockerfile` for dependencies and building.


## Contributing

Sure.
