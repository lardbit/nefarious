# Nefarious

[![Build Status](https://travis-ci.org/lardbit/nefarious.svg?branch=master)](https://travis-ci.org/lardbit/nefarious)

Nefarious is a web application that aims to combine *some* of the features of
[Sonarr](https://github.com/Sonarr/Sonarr/), [Radarr](https://github.com/Radarr/Radarr) and [Ombi](https://github.com/tidusjar/Ombi).

It uses [Jackett](https://github.com/Jackett/Jackett/) under the hood and expects [Transmission](https://transmissionbt.com/) to be running somewhere.

I suggest [docker-transmission-openvpn](https://github.com/haugene/docker-transmission-openvpn) for a dockerized instance of transmission + openvpn.

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
- [ ] Support multiple user permissions (i.e a user must "request" to watch something)
- [ ] Smart Ratio management (auto seed to specified indexers)

### Screenshots

##### Login
![](/screenshots/login.png?raw=true)
##### Search
![](/screenshots/search-blank.png?raw=true)
##### Search Results
![](/screenshots/search-results.png?raw=true)
##### TV Result
![](/screenshots/media-tv-result.png?raw=true)
##### Download Status
![](/screenshots/media-status.png?raw=true)
##### Movie Result
![](/screenshots/media-movie-result.png?raw=true)
##### Movie Custom Quality Profile
![](/screenshots/media-movie-custom-quality-profile.png?raw=true)
##### Discover
![](/screenshots/discover.png?raw=true)
##### Wanted
![](/screenshots/wanted.png?raw=true)
##### Watching
![](/screenshots/watching.png?raw=true)
##### Settings
![](/screenshots/settings.png?raw=true)
##### Search Manual
![](/screenshots/search-manual.png?raw=true)


### Installing

Nefarious is best run via Docker through [Docker Compose](https://docs.docker.com/compose/install/).

Install that and you're all set.

### Running

Run nefarious and dependencies (except transmission):
    
    docker-compose up -d

The default user/pass is `admin/admin`.

**NOTE:** there is an [armv7 image](https://hub.docker.com/r/lardbit/nefarious/tags/) as well.

### Configure Jackett

Configure your local Jackett instance at [http://localhost:9117](http://localhost:9117).  You'll need to add indexers and copy your api key to add in nefarious.

### Configure Nefarious

Open nefarious at [http://localhost:8000](http://localhost:8000).  You'll be redirected to the settings page.

##### Jackett settings

Since jackett is running in the same docker network, you'll need to set the host as `jackett`.  The default port is `9117`.  Enter your api token.

##### Transmission settings

Configure your transmission host, port, username and password, and download directories.  Nefarious will save TV and Movies in individual sub-folders of your configured Transmission download path.

## Debugging
   
    # logs for main app
    docker-compose logs -f nefarious

    # logs for tasks (search results)
    docker-compose logs -f celery
