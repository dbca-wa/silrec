# SILREC — Agents Guide

Django 5.2 + Vue 3 frontend for DBCA WA. Tracks forest compartments, polygons (FEAs), cohorts, treatments, and spatial/operations data.

## Architecture

- **Backend**: Django, DRF, DRF-datatables. API at `/api/` via DRF router in `silrec/urls.py`.
- **Frontend**: Vue 3 + Vite in `silrec/frontend/silrec/`. Built output → `silrec/static/silrec_vue/`.
- **Auth**: SSO via `dbca_utils.middleware.SSOLoginMiddleware`. Dev fallback: `ENABLE_DJANGO_LOGIN=True` enables `LoginView` at `/ssologin/`.
- **Database**: PostgreSQL/PostGIS. Schema via `PGSQL_OPTIONS` env var (`public,silrec` search path). `django.contrib.gis` NOT in INSTALLED_APPS — GIS ops use GeoAlchemy2/SQLAlchemy + raw SQL.
- **Sub-apps**: `forest_blocks` (polygons, cohorts, treatments), `proposals` (lifecycle, shapefile upload/merge/cut), `lookups`, `users`, `main`.

## Developer commands

```bash
# Backend
python manage.py runserver 0.0.0.0:8002
python manage.py shell_plus

# Frontend (in silrec/frontend/silrec/)
npm run dev   # Vite on port 5183 (HMR requires EMAIL_INSTANCE=DEV + DEBUG=True)
npm run build
npm run lint  # ESLint + Prettier via eslint.config.mjs
```

## Vite HMR quirk

`silrec/settings.py:319`: Vite dev mode activates only when `runserver` AND `EMAIL_INSTANCE=DEV` AND `DEBUG=True`. Otherwise Django serves prebuilt static files.

## Tests

```bash
python manage.py test silrec.tests
python manage.py test silrec.components.forest_blocks.tests
```

Most `tests.py` files are empty stubs. The only real test is `tests/test_snapshot_revert.py`. No pytest, no test DB seeding.

## Conventions

- Python: indent 4 spaces, single quotes preferred. No type hints.
- JS/Vue: indent 4 spaces, single quotes, semicolons required, trailing commas.
- `.env` at repo root, read by `confy` in `settings.py`. All config via env vars.
- Migrations in `silrec/migrations/` and per-component.
- No pre-commit hooks or formatter config beyond ESLint.
- Logs: `logs/silrec.log`, `logs/requests.log`, `logs/sys_stats.log`.

## Easy to miss

- `silrec/ordered_model.py` — custom base for ordered models with auto-sequence via DB trigger.
- `silrec/exceptions.py` — custom exception classes.
- Shapefile pipeline: `silrec/components/proposals/` (views, API, service layer).
- **All list endpoints use DRF datatables pagination** — requests must include `draw`, `start`, `length` params.
- `silrec/settings.py:CRS_CARTESIAN` defaults to `epsg:3043`, `CRS_GDA94` to `epsg:28350`.
- Docker build: Azure Pipelines pushes to `dbcawa/silrec` on Docker Hub (main branch only).

## Shapefile workflow buttons (form.vue + workflow_options API)

Button states driven by `GET /api/proposal/<id>/workflow_options/` — returns `actions` object with `enabled`/`reason` for each button, plus `current_status`, `has_shapefile`, `has_processed`, `has_dump`.

| condition | Upload | Process | Revert | Keep |
|---|---|---|---|---|
| no shapefile, status=draft | enabled | disabled | hidden | hidden |
| shapefile exists, status=draft | enabled | enabled | hidden | hidden |
| status=processing_shapefile | disabled | disabled | enabled | enabled |
| user uploads new shapefile | — | sets status=draft, Process re-enabled | — | — |

- **Keep** button sends `POST {transition: 'keep'}` to `workflow_options/` → sets status `with_assessor`, nulls geojson fields
- **Revert** nulls `geojson_data_hist`/`geojson_data_processed`/`geojson_data_processed_iters`, sets status `draft`
- Shapefile buttons only visible in `draft` or `processing_shapefile` status
- Uploaded filename shown read-only in all statuses; delete button only in draft/processing_shapefile
- `POST /api/proposal/<id>/workflow_options/` also handles `transition` field for status changes (to_assessor, to_reviewer, etc.)
- Disabled workflow buttons render light grey via CSS `.workflow-buttons .btn:disabled { background: #d3d3d3 }`
