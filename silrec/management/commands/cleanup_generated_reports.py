import os
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Remove generated report files older than --keep-days days '
        'from file_exports/generated_reports/.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be removed without actually deleting',
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=20,
            help='Remove files older than N days (default 20)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep_days = options['keep_days']

        report_dir = os.path.join(settings.BASE_DIR, settings.REPORT_EXPORT_DIR)

        if not os.path.isdir(report_dir):
            self.stdout.write(f'Directory does not exist: {report_dir}')
            return

        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0

        for f in list(os.listdir(report_dir)):
            fpath = os.path.join(report_dir, f)
            if not os.path.isfile(fpath):
                continue
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff:
                if dry_run:
                    self.stdout.write(f'[dry-run] would remove {f}')
                else:
                    os.remove(fpath)
                    self.stdout.write(f'Removed {f}')
                removed += 1

        if removed == 0:
            self.stdout.write('No files to remove.')
        else:
            self.stdout.write(f'{removed} file(s) {"would be " if dry_run else ""}removed.')
