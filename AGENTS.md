# SILREC — Agents Guide

Django 5.2 + Vue 3 + Vite. Tracks forest compartments, polygons, cohorts, treatments for DBCA WA. API at `/api/`.

## Quick commands

```bash
# Backend (repo root)
python manage.py runserver 0.0.0.0:8002
python manage.py shell_plus

# Frontend (silrec/frontend/silrec/)
npm run dev    # Vite on :5183
npm run build
npm run lint   # ESLint 9 flat config + Prettier
npm ci         # CI uses npm ci --omit=dev (Dockerfile:94)

# Test (only real test)
python manage.py test tests.test_snapshot_revert
```

## Architecture

- Backend: Django, DRF, `django-rest-framework-datatables` — **all list endpoints require `draw`, `start`, `length` query params**.
- Frontend: Vue 3 in `silrec/frontend/silrec/`. Build output → `silrec/static/silrec_vue/`.
- Auth: SSO via `dbca_utils.middleware.SSOLoginMiddleware`. Dev fallback: `ENABLE_DJANGO_LOGIN=True` → login at `/ssologin/`.
- DB: PostgreSQL/PostGIS. `django.contrib.gis` NOT in `INSTALLED_APPS` — GIS via GeoAlchemy2/SQLAlchemy + raw SQL. Search path from `PGSQL_OPTIONS` env var (default `public,silrec`).
- Sub-apps under `silrec/components/`: `forest_blocks` (polygons, cohorts, treatments), `proposals` (lifecycle, shapefile upload/merge/cut), `lookups`, `users`, `main`.
- Entrypoints: `silrec/urls.py` (DRF router + views), `silrec/frontend/silrec/src/main.js` (Vue), `silrec/wsgi.py` (gunicorn).

## Vite HMR

Activates only when all three are true: `runserver` AND `EMAIL_INSTANCE=DEV` AND `DEBUG=True` (`silrec/settings.py:319`). Otherwise Django serves prebuilt static files.

## Conventions

- **Python**: 4-space indent, single quotes preferred, no type hints, no formatter.
- **JS/Vue**: 4-space indent, single quotes, semicolons required, trailing commas (Prettier). ESLint 9 flat config (`eslint.config.mjs` in frontend dir).
- `.env` at repo root, read by `confy` in `settings.py`. All config via env vars.
- Migrations in `silrec/migrations/` plus per-component.
- No pre-commit hooks.
- Logs: `logs/silrec.log`, `logs/requests.log`, `logs/sys_stats.log` (5 MB rotating).
- Vite aliases: `@` → `src/`, `@vue-utils` → `src/utils/vue`, `@common-utils` → `src/components/common/`.

## Easy to miss

- `silrec/ordered_model.py` — custom base for ordered models with auto-sequence via DB trigger.
- CRS defaults: `epsg:3043` (cartesian), `epsg:28350` (GDA94) in `settings.py`.
- Docker: CI (Azure Pipelines, main branch only) pushes to `dbcawa/silrec` + `dbcawa/docker_app_dev`.
- `django-reversion` for audit history.
- CRON managed by external `/bin/scheduler.py` from `dbca-wa/wagov_utils`, config in `cron` file (not django-cron).
- Shapefile pipeline: `silrec/components/proposals/` — views, API, service layer, workflow buttons driven by `GET /api/proposal/<id>/workflow_options/`.
- Only one real test exists: `tests/test_snapshot_revert.py` (TransactionTestCase + SnapshotTestMixin — needs real Postgres, not SQLite). All `tests.py` in sub-apps are empty stubs.
- Gunicorn config in `gunicorn.ini` at repo root. Container entrypoint: `startup.sh` (runs gunicorn on :8080 or cron depending on env vars).
