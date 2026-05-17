import os
import re
import subprocess
import zipfile
import io
from datetime import datetime, timedelta, date
from calendar import monthrange
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Retention helpers                                                  #
# ------------------------------------------------------------------ #

def _is_first_business_day(d):
    """Return True if *d* is the first business day of its month."""
    first = d.replace(day=1)
    # If the 1st is a weekend, the first business day is the next Monday.
    if first.weekday() >= 5:  # Sat=5, Sun=6
        offset = 7 - first.weekday()
        first = first + timedelta(days=offset)
    return d == first


def _parse_dump_timestamp(filename):
    """
    Extract the datetime from a filename like
    silrec_20260513T091500.sql.zip.
    Returns a timezone-naive datetime or None.
    """
    m = re.match(r'^silrec_(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})\.sql\.zip$', filename)
    if not m:
        return None
    try:
        return datetime(int(m[1]), int(m[2]), int(m[3]),
                        int(m[4]), int(m[5]), int(m[6]))
    except (ValueError, IndexError):
        return None


def _files_to_keep(dump_dir, keep_days=14, keep_months_first_business=9):
    """
    Scan dump_dir for silrec_*.sql.zip files and determine which to keep.

    Returns (to_keep, to_remove) — two sets of filenames.
    """
    if not os.path.isdir(dump_dir):
        return set(), set()

    now = datetime.now()
    cutoff = now - timedelta(days=keep_days)

    kept_monthly = set()

    all_files = [f for f in os.listdir(dump_dir) if f.endswith('.sql.zip')]

    # 1. Identify monthly-first-business-day candidates (scoped to the
    #    last *keep_months_first_business* months).
    monthly_cutoff = (now.year, now.month)
    for y, m in _past_n_months(keep_months_first_business, now):
        for f in sorted(all_files):
            ts = _parse_dump_timestamp(f)
            if ts is None:
                continue
            if ts.year == y and ts.month == m:
                candidate_date = ts.date()
                # Check whether the dump was taken on (or close to) the
                # first business day of that month.
                fb = _first_business_day_for_month(y, m)
                # Allow ±1 day tolerance
                if abs((candidate_date - fb).days) <= 1:
                    kept_monthly.add(f)
                    break  # keep at most one per month

    to_keep = set()
    to_remove = set()

    for f in all_files:
        ts = _parse_dump_timestamp(f)
        if ts is None:
            to_remove.add(f)
            continue

        if ts >= cutoff:
            # Within the last keep_days → keep
            to_keep.add(f)
        elif f in kept_monthly:
            # Falls outside keep_days window but qualifies as monthly
            to_keep.add(f)
        else:
            to_remove.add(f)

    return to_keep, to_remove


def _first_business_day_for_month(year, month):
    """Return the date of the first business day for a given month."""
    d = date(year, month, 1)
    while d.weekday() >= 5:  # Sat, Sun
        d += timedelta(days=1)
    return d


def _past_n_months(n, now):
    """Yield (year, month) tuples for the last *n* months (inclusive)."""
    for i in range(n):
        m = now.month - i
        y = now.year
        while m < 1:
            m += 12
            y -= 1
        yield y, m


class Command(BaseCommand):
    help = (
        'pg_dump the database as silrec_yyyymmddThhmmss.sql.zip, '
        'save to file_exports/db_dumps/, apply retention policy.'

	    '- Retention policy (configurable via --keep-days and --keep-monthly):'
		'   - Keeps dumps from the last 14 days'
		'   - Keeps dumps from the first business day of each month for the last 9 months'
		'   - Deletes everything else'

		'DB dumps view at /mgt-commands/db-dumps/'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually dumping',
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=14,
            help='Keep dumps from last N days (default 14)',
        )
        parser.add_argument(
            '--keep-monthly',
            type=int,
            default=9,
            help='Keep monthly first-business-day dumps for N months (default 9)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep_days = options['keep_days']
        keep_monthly = options['keep_monthly']

        dump_dir = os.path.join(settings.BASE_DIR, settings.DB_DUMPS_DIR)
        os.makedirs(dump_dir, exist_ok=True)

        # ---- Retention ----
        to_keep, to_remove = _files_to_keep(dump_dir, keep_days, keep_monthly)

        for f in sorted(to_remove):
            path = os.path.join(dump_dir, f)
            if dry_run:
                self.stdout.write(f'[dry-run] would remove {f}')
            else:
                os.remove(path)
                self.stdout.write(f'Removed {f}')

        if not to_remove:
            self.stdout.write('No files to remove.')

        # ---- Dump ----
        ts = datetime.now().strftime('%Y%m%dT%H%M%S')
        dump_filename = f'silrec_{ts}.sql'
        zip_filename = f'silrec_{ts}.sql.zip'
        dump_path = os.path.join(dump_dir, dump_filename)
        zip_path = os.path.join(dump_dir, zip_filename)

        db_url = settings.DATABASES['default'].get('DATABASE_URL') or os.environ.get('DATABASE_URL', '')
        parsed = urlparse(db_url)
        host = parsed.hostname or 'localhost'
        port = str(parsed.port or 5432)
        db_user = parsed.username or 'dev'
        db_name = parsed.path.lstrip('/') if parsed.path else 'silrec_db'

        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', db_user,
            '-d', db_name,
            '-f', dump_path,
        ]

        if dry_run:
            self.stdout.write(f'[dry-run] would run: {" ".join(cmd)}')
            self.stdout.write(f'[dry-run] would zip to: {zip_path}')
            return

        sub_env = os.environ.copy()
        if parsed.password:
            sub_env['PGPASSWORD'] = parsed.password

        self.stdout.write('Running pg_dump ...')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=sub_env)

        if result.returncode != 0:
            msg = f'pg_dump failed (return code {result.returncode}): {result.stderr}'
            logger.error(msg)
            raise CommandError(msg)

        if not os.path.isfile(dump_path):
            raise CommandError(f'Dump file not created: {dump_path}')

        # Zip the .sql file and remove the plain version
        size_bytes = os.path.getsize(dump_path)
        with open(dump_path, 'rb') as f_in:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(dump_filename, f_in.read())
        os.remove(dump_path)

        self.stdout.write(self.style.SUCCESS(
            f'Created {zip_filename} ({_human_size(size_bytes)})'
        ))


def _human_size(b):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if b < 1024:
            return f'{b:.1f} {unit}'
        b /= 1024
    return f'{b:.1f} TB'
