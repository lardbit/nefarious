### Low memory systems

For single board systems / low memory systems, like the raspberry pi, I recommend only running a single **celery** worker.  Celery is the task/worker component that
handles all the searching and downloading behind the scenes.
    
If you skip this step, **celery** will use every available cpu (ie. the pi v4 has 4 cpus), which I've found is too much for the raspberry pi to handle.

### Specify the number of celery workers

Create a file `.env` at the top level of the folder and enter:

    NUM_CELERY_WORKERS=1
    
Then bring everything back up again:

    docker-compose up -d
