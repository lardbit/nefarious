FROM ubuntu:18.04

EXPOSE 80

# add the main app
ADD src /app

# add the docker entrypoint
ADD docker-entrypoint.sh /app

WORKDIR /app

# NOTE: pattern to sed replace for architecture emulation
#@@cross-build-start@@

# install app dependencies, build app and remove dev dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-venv \
    python3-dev \
    nodejs \
    npm \
    && python3 -m venv /env \
    && /env/bin/pip install --no-cache-dir -r requirements.txt \
    && mkdir -p staticassets && /env/bin/python manage.py collectstatic --no-input \
    && npm --prefix frontend install \
    && npm --prefix frontend run build-prod \
    && apt-get remove -y \
        build-essential \
        nodejs \
        npm \
        python3-venv \
        python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && true

# NOTE: pattern to sed replace for architecture emulation
#@@cross-build-end@@

ENTRYPOINT ["/app/docker-entrypoint.sh"]
