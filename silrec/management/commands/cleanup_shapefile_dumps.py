import os
import glob
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove old pg_dump files from the archive folder, keeping only the most recent SHAPEFILE_EXPORT_KEEP files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=None,
            help='Override SHAPEFILE_EXPORT_KEEP setting',
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='Operate on the archive/ subdirectory instead of the main store',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be deleted without actually removing files',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        use_archive = options['archive']
        keep = options['keep'] if options['keep'] is not None else int(settings.SHAPEFILE_EXPORT_KEEP)

        base_path = os.path.join(settings.BASE_DIR, settings.SHAPEFILE_PROCESSING_STORE)
        if use_archive:
            base_path = os.path.join(base_path, 'archive')

        if not os.path.isdir(base_path):
            self.stdout.write(f"Directory does not exist: {base_path}")
            return

        pattern = os.path.join(base_path, 'silrec_db_pid_*.dump')
        dump_files = sorted(glob.glob(pattern), key=os.path.getmtime)

        self.stdout.write(f"Found {len(dump_files)} dump files in {base_path}, keeping {keep}")

        if len(dump_files) <= keep:
            self.stdout.write("No files to clean up")
            return

        files_to_delete = dump_files[:-keep]
        for fpath in files_to_delete:
            size = os.path.getsize(fpath)
            mtime = os.path.getmtime(fpath)
            if dry_run:
                self.stdout.write(f"  [DRY-RUN] Would delete: {fpath} ({size} bytes, last modified {mtime})")
            else:
                try:
                    os.remove(fpath)
                    self.stdout.write(f"  Deleted: {fpath} ({size} bytes)")
                except OSError as e:
                    self.stdout.write(self.style.ERROR(f"  Failed to delete {fpath}: {e}"))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(files_to_delete)} old dump file(s)"))
