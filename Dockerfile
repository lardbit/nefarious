FROM ubuntu:18.04

EXPOSE 80

# add main app
ADD src /app

# add entrypoints
ADD entrypoint-app.sh /app
ADD entrypoint-celery.sh /app

WORKDIR /app

# install app dependencies, build app and remove dev dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3.8 \
    python3.8-venv \
    python3.8-dev \
    python3.8-gdbm \
    virtualenv \
    gnupg \
    curl \
    git \
    authbind \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install nodejs -y \
    && npm --prefix frontend install \
    && mkdir -p staticassets \
    && npm --prefix frontend run build-prod \
    && python3.8 -m venv /env \
    && /env/bin/pip install --no-cache-dir -r requirements.txt \
    && mkdir -p /nefarious-db \
    && /env/bin/python manage.py collectstatic --no-input \
    && rm -rf frontend/node_modules \
    && apt-get remove -y \
        build-essential \
        nodejs \
        python3.8-venv \
        python3.8-dev \
        virtualenv \
        curl \
        gnupg \
        git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && true

# create non-root user
RUN groupadd -g 10000 nonroot
RUN useradd -g 10000 -u 10000 nonroot
# set file permissions and ownership
RUN chown -R nonroot:nonroot .

# allow non-root user to bind to port 80
RUN touch /etc/authbind/byport/80
RUN chmod 500 /etc/authbind/byport/80
RUN chown nonroot /etc/authbind/byport/80

ENTRYPOINT ["/app/entrypoint-app.sh"]
