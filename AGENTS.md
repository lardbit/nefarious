# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project overview

nefarious is a self-hosted web application that automatically downloads Movies and TV Shows. It searches for torrents via [Jackett](https://github.com/Jackett/Jackett/) and downloads them with [Transmission](https://transmissionbt.com/).

## Tech stack

- **Backend**: Python 3.13, Django 6.1, Django REST Framework 3.18, Celery 5.6, Redis
- **Frontend**: Angular 17, TypeScript 5.2, Bootstrap 5, RxJS 7
- **Key libraries**: `transmission-rpc`, `tmdbsimple`, `django-filter`, `django-redis`, `celery-singleton`, `apprise`

## Commands

The project uses [mise](https://mise.jdx.dev/) to manage tool versions and run tasks. Commands are run via `mise run <task>` (see `mise.toml`).

| Task | Purpose |
|------|---------|
| `mise run install` | Install backend (`install-python`) + frontend (`install-frontend`) dependencies |
| `mise run test` | Run the Django test suite (`cd src && python manage.py test`) |
| `mise run migrate` | Apply Django database migrations |
| `mise run init` | Create the default admin/admin dev user |
| `mise run runserver` | Run the Django development server |
| `mise run asgi` | Run the ASGI server via uvicorn |
| `mise run celery` | Run the Celery worker (DEBUG pauses downloads) |
| `mise run frontend-build` | Build frontend static assets |
| `mise run frontend-watch` | Watch and rebuild frontend static assets |
| `mise run frontend-test` | Run frontend tests |
| `mise run frontend-lint` | Run frontend lint |
| `mise run redis` | Start Redis via Docker Compose |
| `mise run deps` | Start Redis, Jackett, and Transmission via Docker Compose |

Backend tests require a running Redis instance (`mise run redis`) because several tests exercise the cache backend.

## Layout

- `src/nefarious/` — Django application
  - `models.py` — Django models (`WatchMovie`, `WatchTVShow`, `WatchTVSeason`, `WatchTVEpisode`, `WatchTVSeasonRequest`, `NefariousSettings`, etc.)
  - `tasks.py` — Celery tasks (download orchestration, monitoring)
  - `api/` — DRF viewsets, serializers, filters, and views
  - `importer/` — existing-library import logic (movies and TV)
  - `search.py` — Jackett torrent search
  - `processors.py` — media/torrent processing
  - `utils.py` — helpers (renaming, verification, etc.)
- `src/frontend/src/app/` — Angular application (components, services)

## Conventions

- Use the `logger_foreground` / `logger_background` loggers for logging.
- Python code uses type hints.
- No Python linter/formatter (ruff, black, flake8) is configured — match surrounding style.
- The frontend uses tslint (`ng lint`); no ESLint.
- Django settings live in `src/nefarious/settings.py`; environment variables are read from `.env`.

## Notes

- Realtime media updates use Server-Sent Events (SSE): the backend publishes to a Redis pub/sub channel (`src/nefarious/events.py`) and streams to clients via an async SSE endpoint (`src/nefarious/api/events.py`, served at `/api/events/`).
- The frontend syncs media state via SSE (`EventSource`, auth token in query string) and page-visibility polling in `src/frontend/src/app/api.service.ts`.
