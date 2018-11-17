# Nefarious

Nefarious is a web application that aims to combine *some* of the features of
[Sonarr](https://github.com/Sonarr/Sonarr/), [Radarr](https://github.com/Radarr/Radarr) and [Ombi](https://github.com/tidusjar/Ombi).

It uses [Jackett](https://github.com/Jackett/Jackett/) under the hood and expects [Transmission](https://transmissionbt.com/) to be running somewhere.
If you want to run a dockerized instance of transmission + openvpn I suggest [docker-transmission-openvpn](https://github.com/haugene/docker-transmission-openvpn).

Nefarious also needs an API token from [TMDB](http://themoviedb.org).

Features:
- [x] Search TV
- [x] Search Movies
- [x] Auto download TV (individual or full season)
- [x] Auto download Movies
- [x] Manually search Jackett results and download
- [ ] Support multiple user permissions (i.e a user must "request" to watch something)
- [ ] Monitor transmission data results form within the app
- [ ] Auto download media once it's released (routinely scan)

### Running via docker-compose

Copy `.env.template` to `.env` and update accordingly.

Run nefarious and dependencies (except transmission):
    
    docker-compose up -d
    
**NOTE** there is an [armv7 image](https://hub.docker.com/r/lardbit/nefarious/tags/) as well.

### Configure Jackett

Configure your local Jackett instance at [http://localhost:9117](http://localhost:9117).  You'll need to add indexers and copy your api key.

### Configure Nefarious

Open nefarious at [http://localhost:8000](http://localhost:8000).  You'll be redirected to the settings page.

###### Configure jackett

Since jackett is running in the same docker network, you'll need to set the host as `jackett`.  The default port is `9117`.  Enter your api token.

###### Configure transmission

Configure your transmission host, port, username and password, and download directory.  Nefarious will save TV and Movies in a sub-folder of this path.

###### Configure The Movie Database

Configure your TMDB token.  You need to create an account on [http://themoviedb.org](http://themoviedb.org) and request an api token.  You can't continue without one.


## Debugging
   
    # logs for main app
    docker-compose logs -f nefarious

    # logs for tasks (search results)
    docker-compose logs -f celery
