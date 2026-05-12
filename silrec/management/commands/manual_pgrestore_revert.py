import os
import subprocess
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from silrec.components.proposals.models import Proposal, ShapefileProcessing

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Manual pg_restore revert for a proposal.  Resets processing_status to '
        'draft and clears processed geometry fields.  Works regardless of '
        'REVERT_PGDUMP / REVERT_SAVEPOINT setting.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--proposal-id',
            type=int,
            required=True,
            help='Proposal ID to revert',
        )
        parser.add_argument(
            '--dump-file',
            type=str,
            default=None,
            help=(
                'Path to the .dump file.  Defaults to '
                'protected_media/shapefile_processing/silrec_db_pid_<id>.dump'
            ),
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be done without running pg_restore',
        )

    def handle(self, *args, **options):
        proposal_id = options['proposal_id']
        dump_file = options['dump_file']
        dry_run = options['dry_run']

        # Resolve dump file path
        if dump_file:
            dump_filepath = dump_file
        else:
            dump_filepath = os.path.join(
                settings.BASE_DIR,
                settings.SHAPEFILE_PROCESSING_STORE,
                f'silrec_db_pid_{proposal_id}.dump',
            )

        if not os.path.isfile(dump_filepath):
            raise CommandError(f'Dump file not found: {dump_filepath}')

        # Show counts before restore
        self._print_counts('BEFORE RESTORE')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run — pg_restore skipped'))
            return

        # ---- pg_restore ----
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

        self.stdout.write('Running: ' + ' '.join(cmd))

        sub_env = os.environ.copy()
        if parsed.password:
            sub_env['PGPASSWORD'] = parsed.password

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=sub_env)

        if result.returncode != 0:
            msg = f'pg_restore failed (return code {result.returncode}): {result.stderr}'
            self.stdout.write(self.style.ERROR(msg))
            raise CommandError(msg)

        self.stdout.write(self.style.SUCCESS('pg_restore completed successfully'))

        # ---- Reset proposal state ----
        try:
            proposal = Proposal.objects.get(id=proposal_id)
        except Proposal.DoesNotExist:
            raise CommandError(f'Proposal {proposal_id} not found')

        proposal.processing_status = Proposal.PROCESSING_STATUS_DRAFT
        proposal.geojson_data_hist = None
        proposal.geojson_data_processed = None
        proposal.geojson_data_processed_iters = None
        proposal.save()
        self.stdout.write(self.style.SUCCESS(f'Proposal {proposal_id} reset to draft status'))

        # ---- Mark ShapefileProcessing record as restored ----
        try:
            processing = (
                ShapefileProcessing.objects
                .filter(proposal_id=proposal_id, status='completed')
                .order_by('-started_at')
                .first()
            )
            if processing:
                processing.mark_restored()
                self.stdout.write(f'ShapefileProcessing #{processing.id} marked as restored')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not mark restore on db record: {e}'))

        # Show counts after restore
        self._print_counts('AFTER RESTORE')

        self.stdout.write(self.style.SUCCESS(f'Revert complete for proposal {proposal_id}'))

    def _print_counts(self, label):
        self.stdout.write(f'\n--- {label} ---')
        with connection.cursor() as c:
            for tbl in (
                'silrec.polygon',
                'silrec.cohort',
                'silrec.assign_cht_to_ply',
            ):
                c.execute(f'SELECT COUNT(*) FROM {tbl}')
                cnt = c.fetchone()[0]
                self.stdout.write(f'  {tbl:40s} {cnt:>8} rows')
        self.stdout.write('')
