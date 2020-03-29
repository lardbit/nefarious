# Development

If you're interested in developing, contributing or simply want to run nefarious **without** docker then follow these instructions.

nefarious is built on:

- Python 3.8
- Django 3
- Angular 6
- Bootstrap 4

*Note*: Review the [Dockerfile](../Dockerfile) for all the necessary development dependencies.

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

##### Basic development server

This method is the default Django development server but *doesn't support websockets*.

    DEBUG=1 python src/manage.py runserver 8000
   
It'll be now running at [http://127.0.0.1:8000](http://127.0.0.1:8000)

##### Development server with websockets

This method runs the production server (with hot reload) and supports websockets.

Collect all the static assets:

    python src/manage.py collectstatic --noinput
    
Run the server:

    uvicorn nefarious.asgi:application --reload
    
It'll be now running at [http://127.0.0.1:8000](http://127.0.0.1:8000)
   
#### Run celery (task queue)

[Celery](http://celeryproject.org) is a task queue and is used by nefarious to queue downloads, monitor for things, etc.

Run the celery server:

    cd src
    DEBUG=1 celery -A nefarious worker --loglevel=INFO
    
You'll see all download logs/activity come out of here.

**NOTE**: Prefix `WEBSOCKET_HOST=ws://localhost:8000/ws` if you're using the websocket version of the server so the celery tasks can send websocket messages.

**NOTE**: By prefixing `DEBUG=1` before the celery command, all torrents will start as **paused** to avoid downloading anything.

#### Dependencies

Jackett, Redis and Transmission are expected to be running somewhere.  

You can download and run them manually, or, for simplicity, I'd just run them via docker using the `docker-compose.yml` file.

Run redis, jackett and transmission from the `docker-compose.yml` file:

    docker-compose up -d redis jackett transmission
