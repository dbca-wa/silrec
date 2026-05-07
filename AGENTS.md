# SILREC — Agents Guide

Django 5.2 + Vue 3 + Vite. Tracks forest compartments, polygons, cohorts, treatments for DBCA WA. API at `/api/`.

## Quick commands

```bash
# Backend (repo root)
python manage.py runserver 0.0.0.0:8002
python manage.py shell_plus

# Frontend (silrec/frontend/silrec/)
npm run dev    # Vite on :5183
npm run build  # output → silrec/static/silrec_vue/
npm run lint   # ESLint 9 flat config (eslint.config.mjs) + Prettier
npm ci         # CI uses `npm ci --omit=dev` (Dockerfile:94)

# Test (only real test — needs real Postgres)
python manage.py test tests.test_snapshot_revert

# After frontend build, collect new static files:
python manage.py collectstatic --noinput
```

## Architecture

- **Backend**: Django, DRF, `django-rest-framework-datatables` — **all list endpoints require `draw`, `start`, `length` query params**.
- **Frontend**: Vue 3 in `silrec/frontend/silrec/` (not repo root). Build output → `silrec/static/silrec_vue/`.
- **Auth**: SSO via `dbca_utils.middleware.SSOLoginMiddleware`. Dev fallback: `ENABLE_DJANGO_LOGIN=True` → login at `/ssologin/`.
- **DB**: PostgreSQL/PostGIS. `django.contrib.gis` NOT in `INSTALLED_APPS` — GIS via GeoAlchemy2/SQLAlchemy + raw SQL. Search path from `PGSQL_OPTIONS` env var (default `public,silrec`). `USE_TZ = False` (Perth time, no UTC conversion).
- **Sub-apps** under `silrec/components/`: `forest_blocks` (polygons, cohorts, treatments), `proposals` (lifecycle, shapefile upload/merge/cut), `lookups`, `users`, `main`.
- **Entrypoints**: `silrec/urls.py` (DRF router + views), `silrec/frontend/silrec/src/main.js` (Vue), `silrec/wsgi.py` (gunicorn).
- **CI**: Azure Pipelines on main branch only → pushes to `dbcawa/silrec` (production) + `dbcawa/docker_app_dev` (dev).

## Vite HMR

Activates only when all three are true: `runserver` AND `EMAIL_INSTANCE=DEV` AND `DEBUG=True` (`silrec/settings.py:319`). Otherwise Django serves prebuilt static files.

## Conventions

- **Python**: 4-space indent, single quotes preferred, no type hints, no formatter.
- **JS/Vue**: 4-space indent, single quotes, semicolons required, trailing commas (Prettier). ESLint 9 flat config at `silrec/frontend/silrec/eslint.config.mjs`. Root `.eslintrc.json` is stale — ignore it.
- `.env` at repo root, read by `confy` in `settings.py`. All config via env vars.
- Migrations in `silrec/migrations/` plus per-component.
- No pre-commit hooks.
- Logs: `logs/silrec.log`, `logs/requests.log`, `logs/sys_stats.log` (5 MB rotating).
- Vite aliases: `@` → `src/`, `@vue-utils` → `src/utils/vue`, `@common-utils` → `src/components/common/`.

## Easy to miss

- `silrec/ordered_model.py` — custom base for ordered models with auto-sequence via DB trigger.
- CRS defaults: `epsg:3043` (cartesian), `epsg:28350` (GDA94) in `settings.py`.
- `django-reversion` for audit history.
- CRON managed by external `/bin/scheduler.py` from `dbca-wa/wagov_utils`. Config files: `cron` (system crontab with `.cronenv`) and `python-cron` (container-internal scheduler).
- Shapefile pipeline: `silrec/components/proposals/` — views, API, service layer. Workflow buttons driven by `GET /api/proposal/<id>/workflow_options/`.
- Only one real test: `tests/test_snapshot_revert.py` (TransactionTestCase + SnapshotTestMixin — requires real Postgres, not SQLite). All `tests.py` in sub-apps are empty stubs.
- Gunicorn config: `gunicorn.ini` at repo root (max 4 workers, 2048 requests, 600s timeout). Container starts via `startup.sh` (gunicorn on :8080 or cron depending on `ENABLE_WEB`/`ENABLE_CRON` env vars).
- Django admin at `/admin/` (custom `silrec/admin.py`, not `django.contrib.admin`).
