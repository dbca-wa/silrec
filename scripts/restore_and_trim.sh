#!/usr/bin/env bash
# Usage: ./restore_and_trim.sh <backup.sql> <dbname>
#
# Full workflow: clean a pg_dump, restore it, trim trailing spaces,
# and recreate _jn audit triggers.
# Requires PGPASSWORD env var or .pgpass for postgres superuser.

set -euo pipefail

BACKUP="$1"
DBNAME="$2"
CLEANED="/tmp/$(basename "$BACKUP" .sql)_cleaned.sql"

THIS_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Step 1: Clean character(N) -> character varying(N) ==="
"$THIS_DIR/clean_pg_restore.sh" "$BACKUP" "$CLEANED"

echo "=== Step 2: Extract _jn triggers from original backup ==="
python3 -c "
import re
content = open('$BACKUP').read()
# Extract all _jn trigger functions and triggers
funcs = set()
for m in re.finditer(r'(CREATE\s+(OR\s+REPLACE\s+)?FUNCTION\s+\S+_jn_func.*?LANGUAGE\s+plpgsql\s*;)', content, re.DOTALL):
    funcs.add(m.group(1).strip())
triggers = []
for m in re.finditer(r'CREATE\s+TRIGGER\s+(\S+)\s+(BEFORE|AFTER).*?ON\s+(\S+)\s+FOR\s+EACH\s+ROW\s+EXECUTE\s+FUNCTION\s+(\S+\(\))', content, re.DOTALL):
    if 'jn_func' in m.group(4):
        triggers.append(m.group(0))
with open('/tmp/_jn_recreate.sql', 'w') as f:
    f.write('BEGIN;\n\n')
    for func in sorted(funcs):
        f.write(func + '\n\n')
    for t in triggers:
        f.write(t + ';\n\n')
    f.write('COMMIT;\n')
print(f'  Functions: {len(funcs)}, Triggers: {len(triggers)}')
"

echo "=== Step 3: Drop _jn triggers on target DB ==="
python3 -c "
import re
content = open('$BACKUP').read()
triggers = []
for m in re.finditer(r'CREATE\s+TRIGGER\s+(\S+)\s+(BEFORE|AFTER).*?ON\s+(\S+)\s+FOR\s+EACH\s+ROW\s+EXECUTE\s+FUNCTION\s+(\S+\(\))', content, re.DOTALL):
    if 'jn_func' in m.group(4):
        triggers.append((m.group(1), m.group(3)))
with open('/tmp/_jn_drop.sql', 'w') as f:
    f.write('BEGIN;\n')
    for tn, tbl in triggers:
        f.write(f'DROP TRIGGER IF EXISTS {tn} ON {tbl};\n')
    f.write('COMMIT;\n')
" 2>/dev/null

psql -h localhost -U dev -d "$DBNAME" -f /tmp/_jn_drop.sql 2>&1 | tail -3

echo "=== Step 4: Restore cleaned dump ==="
psql -h localhost -U dev -d "$DBNAME" -f "$CLEANED" 2>&1 | tail -5

echo "=== Step 5: Trim trailing spaces ==="
psql -h localhost -U dev -d "$DBNAME" -c "
DO \$\$
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
    BEGIN
      EXECUTE format('UPDATE ONLY %I.%I SET %I = TRIM(%I);',
        r.table_schema, r.table_name, r.column_name, r.column_name);
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'SKIP %.%: %', r.table_name, r.column_name, SQLERRM;
    END;
  END LOOP;
END;
\$\$;
" 2>&1 | tail -5

echo "=== Step 6: Recreate _jn triggers ==="
psql -h localhost -U dev -d "$DBNAME" -f /tmp/_jn_recreate.sql 2>&1 | tail -5

echo "=== Done ==="
