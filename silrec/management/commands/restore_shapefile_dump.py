import os
import subprocess
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from silrec.components.proposals.models import ShapefileProcessing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Restore a pg_dump file (silrec_db_*.dump) for a given proposal using pg_restore'

    def add_arguments(self, parser):
        parser.add_argument(
            '--proposal-id',
            type=int,
            required=True,
            help='Proposal ID to restore the most recent dump for',
        )
        parser.add_argument(
            '--dump-file',
            type=str,
            default=None,
            help='Explicit path to the .dump file (default: most recent for proposal-id)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be done without actually running pg_restore',
        )

    def handle(self, *args, **options):
        proposal_id = options['proposal_id']
        dump_file = options['dump_file']
        dry_run = options['dry_run']

        if dump_file:
            dump_filepath = dump_file
            if not os.path.isfile(dump_filepath):
                raise CommandError(f"Dump file not found: {dump_filepath}")
        else:
            dump_filepath = os.path.join(
                settings.BASE_DIR, settings.SHAPEFILE_PROCESSING_STORE,
                f"silrec_db_pid_{proposal_id}.dump"
            )
            if not os.path.isfile(dump_filepath):
                raise CommandError(
                    f"Dump file for proposal {proposal_id} not found at {dump_filepath}"
                )

        self.stdout.write(f"Using dump file: {dump_filepath}")

        db_url = settings.DATABASES['default'].get('DATABASE_URL') or os.environ.get('DATABASE_URL', '')
        parsed = urlparse(db_url)
        host = parsed.hostname or 'localhost'
        port = str(parsed.port or 5432)
        db_user = parsed.username or 'dev'
        db_name = parsed.path.lstrip('/') if parsed.path else 'silrec_db'

        cmd = [
            'pg_restore',
            '-h', host,
            '-p', port,
            '-U', db_user,
            '-d', db_name,
            '--clean',
            '--if-exists',
            '--no-owner',
            '--no-privileges',
            dump_filepath,
        ]

        self.stdout.write(' '.join(cmd))

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run — no action taken"))
            return

        sub_env = os.environ.copy()
        if parsed.password:
            sub_env['PGPASSWORD'] = parsed.password

        self.stdout.write("Running pg_restore...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=sub_env)

        if result.returncode != 0:
            msg = f"pg_restore failed (return code {result.returncode}): {result.stderr}"
            self.stdout.write(self.style.ERROR(msg))
            raise CommandError(msg)

        # Mark the ShapefileProcessing record as restored
        if not dump_file:
            try:
                processing = ShapefileProcessing.objects.filter(
                    proposal_id=proposal_id, status='completed'
                ).order_by('-started_at').first()
                if processing:
                    processing.mark_restored()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not mark restore on db record: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Restore completed successfully from: {dump_filepath}"))
