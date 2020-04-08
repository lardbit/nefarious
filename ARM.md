## ARM architectures

For those running ARM devices like the raspberry pi, odroid, pine etc, you will need to reference the `docker-compose.arm.yml` file
when running docker commands instead of the default `docker-compose.yml` file.

For example, run the following to bring up all the services on ARM devices: 
    
    docker-compose -f docker-compose.arm.yml up -d
    
### Low memory systems

For single board systems / low memory systems, like the raspberry pi, I recommend only running a single **celery** worker.  Celery is the task/worker component that
handles all the searching and downloading behind the scenes.
    
If you skip this step, **celery** will use every available cpu (ie. the pi v4 has 4 cpus), which I've found is too much for the raspberry pi to handle.

### Specify the number of celery workers

Create a file `.env` at the top level of the folder and enter:

    NUM_CELERY_WORKERS=1
    
Then bring everything back up again:

    docker-compose -f docker-compose.arm.yml up -d
