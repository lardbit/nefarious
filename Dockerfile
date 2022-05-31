FROM ubuntu:22.04

EXPOSE 80

# add main app
ADD src /app

# add entrypoints
ADD entrypoint*.sh /app/

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# install app dependencies, build app and remove dev dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3 \
    python3-venv \
    python3-dev \
    python3-gdbm \
    libpq5 \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    virtualenv \
    gnupg \
    curl \
    git \
    authbind \
    && curl -sL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install nodejs -y \
    && npm --prefix frontend install \
    && npm --prefix frontend run build-prod \
    && mkdir -p staticassets \
    && mkdir -p /nefarious-db \
    && python3 -m venv /env \
    && /env/bin/pip install -U pip \
    && /env/bin/pip install --no-cache-dir --only-binary :all: --extra-index-url https://www.piwheels.org/simple -r requirements.txt \
    && /env/bin/python manage.py collectstatic --no-input \
    && rm -rf frontend/node_modules \
    && apt-get remove -y \
        build-essential \
        cmake \
        nodejs \
        python3-venv \
        python3-dev \
        libpq-dev \
        libffi-dev \
        libssl-dev \
        virtualenv \
        curl \
        gnupg \
        git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && true

ENTRYPOINT ["/app/entrypoint.sh"]
