"""
Dump and restore utilities for shapefile processing rollback functionality.
"""
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

# Tables that get modified by create_gdf()
AFFECTED_TABLES = ['polygon', 'cohort', 'assign_cht_to_ply', 'treatment', 'treatment_xtra']

# Database configuration
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_USER = 'dev'
DB_NAME = 'silrec_test3'
DB_SCHEMA = 'silrec'


def get_db_password():
    """Get database password from environment or settings"""
    return os.environ.get('PGPASSWORD', 'dev123')


def dump_affected_tables(affected_tables, dump_file, schema=DB_SCHEMA):
    """
    Dump specific tables to a file using pg_dump in custom format.

    Args:
        affected_tables: list of dicts with 'table' key OR list of strings
        dump_file: output file path
        schema: PostgreSQL schema name (default: 'silrec')
    """
    # Handle both string and dict inputs
    if affected_tables and isinstance(affected_tables[0], dict):
        affected_names = [t['table'] for t in affected_tables]
    else:
        affected_names = affected_tables

    # Build command with multiple -t flags, use -Fc for custom format
    cmd = [
        'pg_dump', '-h', DB_HOST, '-p', DB_PORT, '-U', DB_USER,
        '-d', DB_NAME,
        '-Fc',  # custom format (required for pg_restore)
        '-f', dump_file,
    ]
    # Add -t for each table with schema prefix
    for t in affected_names:
        cmd.extend(['-t', f'{schema}.{t}'])

    env = os.environ.copy()
    env['PGPASSWORD'] = get_db_password()

    print(f"Dumping affected tables: {affected_names}")
    subprocess.run(cmd, env=env, check=True)
    print(f"Dumped to: {dump_file}")


def restore_affected_tables(affected_tables, dump_file, schema=DB_SCHEMA):
    """
    Restore specific tables from a dump file using pg_restore.

    Args:
        affected_tables: list of table names (strings) OR list of dicts with 'table' key
        dump_file: input file path
        schema: PostgreSQL schema name (default: 'silrec')
    """
    # Handle both string and dict inputs
    if affected_tables and isinstance(affected_tables[0], dict):
        affected_names = [t['table'] for t in affected_tables]
    else:
        affected_names = affected_tables

    # Restore dependent tables first (FK order matters)
    # order: polygon -> cohort -> assign_cht_to_ply
    table_order = ['polygon', 'cohort', 'assign_cht_to_ply']

    env = os.environ.copy()
    env['PGPASSWORD'] = get_db_password()

    for table_name in table_order:
        if table_name not in affected_names:
            continue

        cmd = [
            'pg_restore', '-h', DB_HOST, '-p', DB_PORT, '-U', DB_USER,
            '-d', DB_NAME,
            '--disable-triggers',  # disable triggers during restore
            dump_file,
            '--clean',  # clean (drop)
            '--if-exists',  # don't error if doesn't exist
            '-v',  # don't error if doesn't exist
        ]
            #'-t', f'{schema}.{table_name}',

        #pg_restore -h localhost -p 5432 -U dev -d silrec_test3 -1 --disable-triggers silrec_3tables_14Mar2026.dump -v --clean --if-exists


        print(f"CMD: {cmd}")
        print(f"Restoring table: {table_name}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            raise subprocess.CalledProcessError(result.returncode, cmd)

    print(f"Restored from: {dump_file}")


def cleanup_old_dumps(directory, max_age_hours=24):
    """
    Clean up old dump files from a directory.

    Args:
        directory: Path to the dump directory
        max_age_hours: Maximum age in hours for files to keep
    """
    import time

    if not os.path.exists(directory):
        return 0

    cutoff_time = time.time() - (max_age_hours * 3600)
    cleaned_count = 0

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_age = os.path.getmtime(filepath)
            if file_age < cutoff_time:
                os.remove(filepath)
                cleaned_count += 1
                print(f"Removed old dump: {filename}")

    return cleaned_count
