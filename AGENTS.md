# AGENTS.md

## Architecture

- **Django 4.2+ (app server) + Angular 17 (frontend)** monorepo. (The settings.py docstring still says "Django 3.0" — ignore that, the real version is in `requirements.txt`.)
- Django entrypoint: `src/manage.py` — all `manage.py` commands run from the repo root, e.g. `python src/manage.py test`.
- The Django project package is `src/nefarious/`, settings at `src/nefarious/settings.py`.
- **ASGI** via `uvicorn`, not WSGI. Supports websockets. Port 80 in Docker, 8000 locally.
- **Celery** task queue (downloads, monitoring), broker is **Redis**. Worker and beat scheduler are separate containers by default (`CELERY_BEAT_SEPARATELY=1` in the compose base file).
- Frontend builds output to `src/staticassets/` which Django serves as a static directory. Standard Angular CLI tooling in `src/frontend/`.

## Configuration

- **All settings come from `.env`** (copy from `env.template`). Never edit compose yaml files directly.
- `DEBUG=1` env var enables Django debug mode **and** makes celery start all torrents as **paused** (prevents accidental downloads during development).

## Dev commands (run from repo root)

```sh
# Python deps
pip install -r src/requirements.txt

# Init DB and create default admin user
python src/manage.py migrate
python src/manage.py nefarious-init admin admin@localhost admin

# Frontend (npm works from repo root via --prefix)
npm --prefix src/frontend install
npm --prefix src/frontend run build         # one-shot
npm --prefix src/frontend run watch         # auto-rebuild on changes

# Django dev server (NO websocket support)
DEBUG=1 python src/manage.py runserver 8000

# Uvicorn (WITH websocket support — requires collectstatic first)
python src/manage.py collectstatic --noinput
uvicorn nefarious.asgi:application --reload

# Celery worker (must be run from src/ directory)
cd src && DEBUG=1 celery -A nefarious worker --loglevel=INFO

# For websocket dev, set this env var on celery too:
# WEBSOCKET_HOST=ws://localhost:8000/ws
```

## Testing

- **Django backend tests** use `TestCase`, located in `src/nefarious/tests/`.
- **Tests require Redis.** CI runs them inside a Docker container on a shared network with a Redis container:
  ```sh
  docker run --network tests -e REDIS_HOST=redis --entrypoint /env/bin/python lardbit/nefarious:latest manage.py test
  ```
- Locally, make sure Redis is reachable (default `localhost:6379`) before running `python src/manage.py test`.
- **Frontend unit tests** (Karma + Jasmine):
  ```sh
  npm --prefix src/frontend run test -- --browsers=ChromeHeadless --watch=false
  ```
  All spec files are in `src/frontend/src/app/`. A shared mock helper is at `src/frontend/src/app/test-helpers.ts`.
- **Frontend e2e tests** (Playwright) — needs the built Angular app served at `http://localhost:8000/static/`. Either run Django (`python src/manage.py runserver 8000`) after `collectstatic`, or serve `src/staticassets/` directly with a static server under a `/static/` path:
  ```sh
  npm --prefix src/frontend run build
  mkdir -p serve/static && cp -r src/staticassets/* serve/static/
  python3 -m http.server 8000 --directory serve &
  npm --prefix src/frontend run e2e
  ```
  Specs in `src/frontend/e2e/`. Config at `src/frontend/playwright.config.ts`.
- **Full-stack e2e** specs are also in `src/frontend/e2e/fullstack.spec.ts` — they test both the API endpoints and the Angular SPA against the live server.

## Docker / CI

- Two-stage Docker build: `Dockerfile-frontend` builds the Angular app first, then `Dockerfile` copies its output from the frontend image. The frontend image must be built and tagged before the app image.
- CI workflow: `.github/workflows/build.yml`. On push and pull_request, it runs two parallel jobs:
  - `test-frontend`: Karma unit tests + Playwright e2e tests
  - `build`: builds both Docker images, runs Django tests in Docker against a Redis container, then pushes multi-arch (amd64 + arm64) images to Docker Hub.
- Dev compose: `docker-compose.yml` (uses `docker-compose.base.yml` for shared service templates).

## Other notes

- `tmdbsimple` is installed from a forked repo: `git+https://github.com/lardbit/tmdbsimple.git` (in requirements.txt).
- Database default is SQLite (`DATABASE_URL` env var uses `dj-database-url`).
- Video detection uses opencv (`opencv-contrib-python-headless`), which requires system libs (libav*, libhdf5, etc.) installed via apt in the Dockerfile.
- Custom management commands in `src/nefarious/management/commands/`: `nefarious-init`, `import-media`, `re-test-movie`, `re-test-tv`, `video-detection`.
- Reference docs: `docs/DEVELOPMENT.md`, `docs/USAGE.md`, `docs/TROUBLESHOOTING.md`, `docs/DEPENDENCIES.md`, `docs/VPN.md`, `docs/SBC.md`.
