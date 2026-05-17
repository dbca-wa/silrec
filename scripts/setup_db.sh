#!/usr/bin/env bash
# Setup SILREC database from a v3 backup.
#
# Usage:
#   ./scripts/setup_db.sh                        # uses defaults
#   DB_NAME=my_db DB_USER=me ./scripts/setup_db.sh
#
# Required variables (set via env or edit defaults below):
set -euo pipefail

DB_NAME="${DB_NAME:-silrec_test2}"
DB_SCRIPT="${DB_SCRIPT:-$HOME/projects/silrec/scripts/silrec_db_create.sql}"
RESTORE_FILE="${RESTORE_FILE:-$HOME/projects/tmp/silrec_v3_backup_04May2026.sql}"
REVERT_DUMP_FILE="${REVERT_DUMP_FILE:-$HOME/projects/tmp/silrec_3tables_04May2026_v2.dump}"

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


#echo "=== 0. Clean the restore file ==="

#if [ -f "$RESTORE_FILE" ]; then
#    sed -i '/silrec_user/d' "$RESTORE_FILE"
#    sed -i '/silrec_mgr/d' "$RESTORE_FILE"
#    sed -i '/johnm/d' "$RESTORE_FILE"
#    sed -i '/shelleyp/d' "$RESTORE_FILE"
#
#    sed -i 's/CREATE SCHEMA silrec_v3;/CREATE SCHEMA silrec;/g' "$RESTORE_FILE"
#    sed -i "s/ALTER SCHEMA silrec_v3 OWNER TO postgres;/ALTER SCHEMA silrec OWNER TO ${DB_USER};/g" "$RESTORE_FILE"
#    sed -i 's/silrec_v3\./silrec./g' "$RESTORE_FILE"
#    sed -i 's/compartmen character/compartment character/g' "$RESTORE_FILE"
#    sed -i 's/reason_clo character/reason_closed character/g' "$RESTORE_FILE"
#    sed -i 's/current_status/status_current/g' "$RESTORE_FILE"
#    sed -i "s/OWNER TO postgres/OWNER TO ${DB_USER}/g" "$RESTORE_FILE"
#    sed -i 's/updated_on timestamp without time zone/updated_on timestamp/g' "$RESTORE_FILE"
#    sed -i 's/created_on timestamp without time zone/created_on timestamp/g' "$RESTORE_FILE"
#else
#    echo "WARNING: RESTORE_FILE not found at $RESTORE_FILE — skipping cleanup"
#fi

echo "=== 1.1 Create the database ==="
PGPASSWORD="" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_SUPERUSER" -W \
    -v db_name="$DB_NAME" -v db_user="$DB_USER" -v db_pass="$DB_PASS" \
    -f "$DB_SCRIPT"

echo "=== 1.2 Restore from backup ==="
if [ -f "$RESTORE_FILE" ]; then
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$RESTORE_FILE"
else
    echo "WARNING: RESTORE_FILE not found at $RESTORE_FILE — skipping restore"
fi

PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d $DB_NAME \
    -c "ALTER TABLE polygon RENAME COLUMN compartmen TO compartment;"

#PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d $DB_NAME \
#    -c "ALTER TABLE polygon RENAME COLUMN reason_clo TO reason_closed;"

echo "=== 2. Apply migrations ==="
cd $HOME/projects/silrec
source venv/bin/activate
./manage.py migrate lookups 0001 --fake
./manage.py migrate forest_blocks 0001 --fake
./manage.py migrate lookups
./manage.py migrate silrec
./manage.py migrate forest_blocks
./manage.py migrate

echo "=== 3. Create default users ==="
./manage.py shell_plus <<'PYEOF'
#import os
#from django.contrib.auth.models import User
#
#users = [
#    ('jawaidm',  'jawaid',  'mushtaq',     'jawaid.mushtaq@dbca.wa.gov.au',     'jm',   True,  True),
#    ('nouser',   'nouser',  'nouser_group', 'nouser@dbca.wa.gov.au',             'test', True,  False),
#    ('user',     'user',    'user_group',   'user@dbca.wa.gov.au',               'test', True,  False),
#    ('operator', 'operator','operator_group','operator@dbca.wa.gov.au',          'test', True,  False),
#    ('assessor', 'assessor','assessor_group','assessor@dbca.wa.gov.au',          'test', True,  False),
#    ('reviewer', 'reviewer','reviewer_group','reviewer@dbca.wa.gov.au',          'test', True,  False),
#    ('silrec_admin', 'silrec_admin', 'silrec_admin_group', 'silrec_admin@dbca.wa.gov.au', 'test', True,  False),
#]
#for username, first, last, email, pw, staff, superuser in users:
#    u, created = User.objects.get_or_create(username=username, defaults={
#        'first_name': first, 'last_name': last, 'email': email,
#        'is_staff': staff, 'is_superuser': superuser,
#    })
#    if created:
#        u.set_password(pw)
#        u.save()
#        print(f'Created user: {username}')
#    else:
#        print(f'User exists: {username}')

from silrec.components.forest_blocks.models import ObjectiveLkp, Cohort
ObjectiveLkp.objects.get_or_create(obj_code='NOTDEF')
Cohort.objects.get_or_create(cohort_id=1, defaults={'obj_code': 'NOTDEF', 'regen_method_id': ' %'})
print('Default cohort and objective created.')
PYEOF

echo "=== 4. Load fixtures ==="
./manage.py loaddata silrec/fixtures/user_group.json
./manage.py loaddata silrec/fixtures/application_type.json silrec/fixtures/proposal_type.json
./manage.py loaddata silrec/fixtures/proposal.json silrec/fixtures/textsearch.json silrec/fixtures/shpfile_attrs_config.json
./manage.py loaddata silrec/fixtures/sqlreport_v2.json silrec/fixtures/form_validation_rules.json


echo "=== 5. Dump 3 tables for revert testing ==="
PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    -t silrec.assign_cht_to_ply -t silrec.cohort -t silrec.polygon \
    -Fc -f "$REVERT_DUMP_FILE"

echo "=== 6. Create Backup DB ==="
BACKUP_DB="${DB_NAME}_$(date +%Y%m%d)"
PGPASSWORD="$DB_SUPERUSER" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_SUPERUSER" -d postgres \
    -c "CREATE DATABASE \"$BACKUP_DB\" WITH TEMPLATE \"$DB_NAME\";"
echo "Backup DB '$BACKUP_DB' created from template '$DB_NAME'"

echo "=== Done ==="
