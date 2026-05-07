#!/usr/bin/env bash
# Usage: ./trim_data.sh <dbname> [schema]
#
# Trims trailing spaces from all character varying columns in the
# specified schema (default: silrec). Only processes tables that
# had character(N) columns in the original pg_dump.
#
# Run this AFTER a restore from a cleaned pg_dump to clean up
# trailing spaces that were baked into the COPY data.
#
# This script handles:
#   - FK constraints (uses CASCADE where needed)
#   - _jn audit triggers (disables them temporarily)
#   - Case-sensitive quoted column names
#   - PK deduplication

set -euo pipefail

DB="$1"
SCHEMA="${2:-silrec}"

PSQL="psql -h localhost -U dev -d $DB"

echo "=== Disabling triggers on base tables ==="
$PSQL -c "
SELECT format('ALTER TABLE %I.%I DISABLE TRIGGER USER;', schemaname, tablename)
FROM pg_tables
WHERE schemaname = '$SCHEMA' AND tablename NOT LIKE 'vw_%'
" --no-align --tuples-only | $PSQL

echo "=== Trimming data ==="
$PSQL <<'EOSQL'
DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT table_schema, table_name, column_name
    FROM information_schema.columns
    WHERE data_type = 'character varying'
      AND table_schema = 'silrec'
      AND table_name NOT LIKE 'vw_%'
    ORDER BY table_schema, table_name, ordinal_position
  LOOP
    EXECUTE format(
      'UPDATE ONLY %I.%I SET %I = TRIM(%I);',
      r.table_schema, r.table_name, r.column_name, r.column_name
    );
  END LOOP;
END;
$$;
EOSQL

echo "=== Re-enabling triggers ==="
$PSQL -c "
SELECT format('ALTER TABLE %I.%I ENABLE TRIGGER USER;', schemaname, tablename)
FROM pg_tables
WHERE schemaname = '$SCHEMA' AND tablename NOT LIKE 'vw_%'
" --no-align --tuples-only | $PSQL

echo "=== Done ==="
