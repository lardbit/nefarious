# Troubleshooting

Logs for main app

    docker-compose logs -f nefarious

Logs for tasks (search results):

    docker-compose logs -f celery

List all services (they should all be "up"):

    docker-compose ps

Completely restart everything (you won't lose your nefarious settings, though):

    docker-compose down
    docker-compose up -d

## FAQ
### Nefarious says my content is downloaded, but I cannot find it

After your content is downloaded, transmission places it in `.unprocessed-nefarious-downloads`. Periodically (see [tasks.py](https://github.com/lardbit/nefarious/blob/f76d9d429b94e740a5a3d043ea1b70fedab2e9c3/src/nefarious/tasks.py#L33)) a job is run that among other things moves the file to the correct folder. You can manually trigger this task via `Process Completed Media` in the settings page.
