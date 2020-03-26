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


