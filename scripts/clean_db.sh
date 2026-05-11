#!/usr/bin/env bash
# Setup SILREC database from a v3 backup.
#
# Usage:
#   ./scripts/setup_db.sh                        # uses defaults
#   DB_NAME=my_db DB_USER=me ./scripts/setup_db.sh
#
# Required variables (set via env or edit defaults below):
set -euo pipefail

RESTORE_FILE="${RESTORE_FILE:-$HOME/projects/tmp/silrec_v3_backup_04May2026.sql}"

# Parse DATABASE_URL from .env if set, otherwise use defaults
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
    DATABASE_URL="$(grep -E '^DATABASE_URL=' "$ENV_FILE" | head -1 | sed 's/^DATABASE_URL=//; s/^"//; s/"$//')"
fi
if [ -n "${DATABASE_URL:-}" ]; then
    DB_USER="$(echo "$DATABASE_URL" | sed 's|.*://||; s|:.*||')"
    DB_PASS="$(echo "$DATABASE_URL" | sed 's|.*://[^:]*:||; s|@.*||')"
    DB_HOST="$(echo "$DATABASE_URL" | sed 's|.*@||; s|:.*||')"
    DB_PORT="$(echo "$DATABASE_URL" | sed 's|.*:||; s|/.*||')"
else
    DB_USER="${DB_USER:-<user>}"
    DB_PASS="${DB_PASS:-<passwd>}"
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
fi
DB_SUPERUSER="${DB_SUPERUSER:-postgres}"


echo "=== 0. Clean the restore file ==="

if [ -f "$RESTORE_FILE" ]; then
    sed -i '/silrec_user/d' "$RESTORE_FILE"
    sed -i '/silrec_mgr/d' "$RESTORE_FILE"
    sed -i '/johnm/d' "$RESTORE_FILE"
    sed -i '/shelleyp/d' "$RESTORE_FILE"

    sed -i 's/CREATE SCHEMA silrec_v3;/CREATE SCHEMA silrec;/g' "$RESTORE_FILE"
    sed -i "s/ALTER SCHEMA silrec_v3 OWNER TO postgres;/ALTER SCHEMA silrec OWNER TO ${DB_USER};/g" "$RESTORE_FILE"
    sed -i 's/silrec_v3./silrec./g' "$RESTORE_FILE"
#    sed -i 's/compartmen character/compartment character/g' "$RESTORE_FILE"
#    sed -i 's/reason_clo character/reason_closed character/g' "$RESTORE_FILE"
    sed -i 's/current_status/status_current/g' "$RESTORE_FILE"
    sed -i "s/OWNER TO postgres/OWNER TO ${DB_USER}/g" "$RESTORE_FILE"
    sed -i 's/updated_on timestamp without time zone/updated_on timestamp/g' "$RESTORE_FILE"
    sed -i 's/created_on timestamp without time zone/created_on timestamp/g' "$RESTORE_FILE"
else
    echo "WARNING: RESTORE_FILE not found at $RESTORE_FILE — skipping cleanup"
fi

echo "=== Done ==="
