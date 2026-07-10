# Development

If you're interested in developing, contributing or simply want to run nefarious **without** docker then follow these instructions.

nefarious is built on:

- Python 3.9
- Django 3
- Angular 17
- Bootstrap 5

*Note*: Review the [Dockerfile](../Dockerfile) for all the necessary development dependencies.

#### Install development tools

The project uses [mise](https://mise.jdx.dev/) to install and select the local development tools. The committed `mise.toml` pins Python and Node to the versions used by the Dockerfiles, and installs `uv` for Python environment/dependency work.

    mise trust
    mise install

Run commands through `mise run <task>` or activate mise in your shell before using `python`, `uv`, `npm`, or `docker-compose` directly.

#### Install python dependencies

mise creates and activates a local `.venv` using `uv`.
  
    mise run install-python

To install both backend and frontend dependencies:

    mise run install

#### Start development dependencies

Jackett, Redis and Transmission are expected to be running somewhere.

You can download and run them manually, or, for simplicity, run them via Docker Compose. The mise tasks include `docker-compose.dev.yml`, which publishes Redis on `localhost:6379` for local Django and Celery processes.

To start Redis only:

    mise run redis

Before starting the full dependency stack, create a local `.env` file and adjust it for your development machine:

    cp env.template .env

At minimum, review `HOST_DOWNLOAD_PATH`, `HOST_DOWNLOAD_UID`, and `HOST_DOWNLOAD_GID`. If you are developing with VPN-backed Transmission, also fill in the `OPENVPN_*`, `LOCAL_NETWORK`, and `VPN_IPV6_DISABLED` settings as applicable.

Then run Redis, Jackett and Transmission:

    mise run deps

#### Build database
  
    mise run migrate

#### Run nefarious init script

This creates a default user and pass (admin/admin).

    mise run init


#### Build front-end resources

First install the frontend dependencies:

    mise run install-frontend

Then build the frontend html/css stuff (angular):
    
    mise run frontend-build
   
Note: run `mise run frontend-watch` to automatically rebuild while you're developing the frontend stuff.
   
#### Run nefarious

##### Basic development server

This method is the default Django development server but *doesn't support websockets*.

    mise run runserver
   
It'll be now running at [http://127.0.0.1:8000](http://127.0.0.1:8000)

##### Development server with websockets

This method runs the production server (with hot reload) and supports websockets.

Collect all the static assets:

    mise run collectstatic
    
Run the server:

    mise run asgi
    
It'll be now running at [http://127.0.0.1:8000](http://127.0.0.1:8000)
   
#### Run celery (task queue)

[Celery](http://celeryproject.org) is a task queue and is used by nefarious to queue downloads, monitor for things, etc.

Run the celery server:

    mise run celery
    
You'll see all download logs/activity come out of here.

**NOTE**: Prefix `WEBSOCKET_HOST=ws://localhost:8000/ws` if you're using the websocket version of the server so the celery tasks can send websocket messages.

**NOTE**: By prefixing `DEBUG=1` before the celery command, all torrents will start as **paused** to avoid downloading anything.

#### Stop development services

Stop Docker Compose services and any local dev processes started by the mise tasks:

    mise run dev-down
