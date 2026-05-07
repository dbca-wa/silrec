#!/usr/bin/env bash
# Usage: ./clean_pg_restore.sh <input.sql> [output.sql]
#
# Replaces all 'character(N)' column types with 'character varying(N)'
# in a pg_dump SQL file. This prevents trailing-space padding issues
# when restoring into Django-managed tables (Django CharField = varchar).
#
# Run the output file with psql instead of the original dump.
# Then run trim_pg_restore.sh against the restored database to clean
# trailing spaces from the data that was already in the backup.
#
# If no output file is given, the input file is edited in place.

set -euo pipefail

input="$1"
output="${2:-}"

if [ -z "$output" ]; then
    tmp=$(mktemp)
    sed -E 's/^([[:space:]]*[[:alnum:]_"]+)[[:space:]]+character\(([0-9]+)\)/\1 character varying(\2)/g' "$input" > "$tmp"
    mv "$tmp" "$input"
    echo "Cleaned in place: $input"
else
    sed -E 's/^([[:space:]]*[[:alnum:]_"]+)[[:space:]]+character\(([0-9]+)\)/\1 character varying(\2)/g' "$input" > "$output"
    echo "Cleaned: $input -> $output"
fi
