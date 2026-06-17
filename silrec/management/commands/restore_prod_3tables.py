import os
import subprocess
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.db import connection
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
      ./manage.py restore_prod_tables --path shared/silrec_3tables_04May2026_v2.dump
    '''
    help = 'Drop polygon/cohort/assign_cht_to_ply tables and pg_restore from a dump file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Path to the .dump file (e.g. shared/silrec_3tables_04May2026_v2.dump)',
        )
        parser.add_argument(
            '--skip-drop',
            action='store_true',
            help='Skip dropping tables before restore',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be done without actually running',
        )

    def handle(self, *args, **options):
        dump_file = options['path']
        skip_drop = options['skip_drop']
        dry_run = options['dry_run']

        if not os.path.isfile(dump_file):
            raise CommandError(f'Dump file not found: {dump_file}')

        db_conf = settings.DATABASES['default']
        db_url = db_conf.get('DATABASE_URL') or os.environ.get('DATABASE_URL', '')
        parsed = urlparse(db_url)
        host = parsed.hostname or 'localhost'
        port = str(parsed.port or 5432)
        db_user = parsed.username or 'dev'
        db_name = parsed.path.lstrip('/') if parsed.path else 'silrec_db'
        password = parsed.password

        if not skip_drop:
            self.stdout.write('Dropping existing polygon, cohort, assign_cht_to_ply tables...')
            if dry_run:
                self.stdout.write(self.style.WARNING('  (dry-run — would drop)'))
            else:
                with connection.cursor() as cursor:
                    cursor.execute('DROP TABLE IF EXISTS assign_cht_to_ply CASCADE')
                    cursor.execute('DROP TABLE IF EXISTS polygon CASCADE')
                    cursor.execute('DROP TABLE IF EXISTS cohort CASCADE')
                self.stdout.write(self.style.SUCCESS('  Done.'))

        cmd = [
            'pg_restore',
            '-h', host,
            '-p', port,
            '-U', db_user,
            '--no-owner',
            '--role', db_user,
            '-d', db_name,
            dump_file,
        ]

        self.stdout.write(f'Running: {" ".join(cmd)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run — no action taken'))
            return

        sub_env = os.environ.copy()
        if password:
            sub_env['PGPASSWORD'] = password

        self.stdout.write('Running pg_restore...')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=sub_env)

        for line in result.stdout.splitlines():
            self.stdout.write(f'  {line}')

        if result.returncode != 0:
            msg = f'pg_restore failed (return code {result.returncode}): {result.stderr}'
            self.stdout.write(self.style.ERROR(msg))
            raise CommandError(msg)

        self.stdout.write(self.style.SUCCESS(f'Restore completed from: {dump_file}'))
