FROM resin/armv7hf-ubuntu

WORKDIR /app

# copy pre-built app from base image
COPY --from=lardbit/nefarious /app .

RUN ["cross-build-start"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-dev \
    python3-venv \
    python3-gdbm \
    && python3 -m venv /env \
    && /env/bin/pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y \
        build-essential \
        python3-venv \
        python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && true

RUN ["cross-build-end"]

EXPOSE 80

ENTRYPOINT ["/app/docker-entrypoint.sh"]
