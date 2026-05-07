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

# After frontend build, collect new static files:
python manage.py collectstatic --noinput

# Test (only real test — needs real Postgres, not SQLite)
python manage.py test tests.test_snapshot_revert

# DB model graph (requires pydotplus + graphviz):
# ./manage.py graph_models silrec --include-models silrec.cohort -o /tmp/silrec_models.png
```

## Architecture

- **Backend**: Django, DRF, `django-rest-framework-datatables` — all list endpoints require `draw`, `start`, `length` query params. DRF router in `silrec/urls.py:27`.
- **Frontend**: Vue 3 at `silrec/frontend/silrec/` (not repo root). Build output → `silrec/static/silrec_vue/`. Entry: `src/main.js:1`.
- **Auth**: SSO via `dbca_utils.middleware.SSOLoginMiddleware`. Dev fallback: `ENABLE_DJANGO_LOGIN=True` → login at `/ssologin/`.
- **DB**: PostgreSQL/PostGIS. `django.contrib.gis` NOT in `INSTALLED_APPS` — GIS via GeoAlchemy2 + raw SQL. Search path from `PGSQL_OPTIONS` env var (default `public,silrec`). `USE_TZ = False` (Perth time, no UTC conversion).
- **Sub-apps** under `silrec/components/`: `forest_blocks` (polygons, cohorts, treatments), `proposals` (lifecycle, shapefile upload/merge/cut), `lookups`, `users`, `main`.
- **Entrypoints**: `silrec/urls.py` (DRF router + views), `silrec/frontend/silrec/src/main.js` (Vue), `silrec/wsgi.py` (gunicorn).
- **CI**: Azure Pipelines on main branch only → pushes to `dbcawa/silrec` (production) + `dbcawa/docker_app_dev` (dev).
- **Docker**: gunicorn on `:8080`, max 4 workers, 2048 requests, 600s timeout (`gunicorn.ini`). Container starts via `startup.sh` — gunicorn or cron depending on `ENABLE_WEB`/`ENABLE_CRON`.

## Vite HMR

Activates only when all three are true: `runserver` AND `EMAIL_INSTANCE=DEV` AND `DEBUG=True` (`silrec/settings.py:319`). Otherwise Django serves prebuilt static files.

## Conventions

- **Python**: 4-space indent, single quotes preferred, no type hints, no formatter.
- **JS/Vue**: 4-space indent, single quotes, semicolons required, trailing commas (Prettier at `.prettierrc`). ESLint 9 flat config at `silrec/frontend/silrec/eslint.config.mjs`. Root `.eslintrc.json` is stale — ignore it.
- `.env` at repo root, read by `confy` in `settings.py` and `wsgi.py`. All config via env vars.
- Migrations in `silrec/migrations/` plus per-component.
- No pre-commit hooks.
- Logs: `logs/silrec.log`, `logs/requests.log`, `logs/sys_stats.log` (5 MB rotating).
- Vite aliases: `@` → `src/`, `@vue-utils` → `src/utils/vue`, `@common-utils` → `src/components/common/`.

## Easy to miss

- `silrec/admin.py` (custom `AdminSite`, NOT `django.contrib.admin`) — imports `django.contrib.gis.admin` for `GeometryField` awareness, registers `FormValidationRule`.
- `silrec/ordered_model.py` — custom abstract base for ordered models with auto-sequence via DB trigger.
- CRS defaults: `epsg:3043` (cartesian), `epsg:28350` (GDA94) in `settings.py:43-44`.
- `django-reversion` for audit history — middleware at `silrec/middleware.py`.
- CRON managed by external `/bin/scheduler.py` from `dbca-wa/wagov_utils`. Config: `python-cron` (container-internal scheduler), `cron` (system crontab). Tasks: `cron_tasks`, `update_cache`, `task_runner`, `runcrons`, `appmonitor_check`.
- Shapefile pipeline: `silrec/components/proposals/` — views, API, service layer. Workflow buttons driven by `GET /api/proposal/<id>/workflow_options/`.
- Only one real test: `tests/test_snapshot_revert.py` (TransactionTestCase + SnapshotTestMixin — requires real Postgres). All `tests.py` in sub-apps are empty stubs.
- `settings.py:425` — `SHAPEFILE_PROCESSING_STORE` env var defaults to `protected_media/shapefile_processing`. `SHAPEFILE_EXPORT_KEEP` defaults to 10.
- DB: `DATABASE_URL` uses `postgis://` scheme (dj-database-url). SQLite route is commented out — will not work with PostGIS-dependent code.
- Dev user creation: `manage.py shell_plus` → `User.objects.create(email=..., username=..., first_name=..., last_name=...)` + `u.set_password(...)`.
