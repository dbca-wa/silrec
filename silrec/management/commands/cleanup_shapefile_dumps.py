import os
import glob
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove old pg_dump files from the shapefile processing store, keeping only the most recent SHAPEFILE_EXPORT_KEEP files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=None,
            help='Override SHAPEFILE_EXPORT_KEEP setting',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be deleted without actually removing files',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep = options['keep'] if options['keep'] is not None else int(settings.SHAPEFILE_EXPORT_KEEP)
        store_path = os.path.join(settings.SHAPEFILE_PROCESSING_STORE)

        if not os.path.isdir(store_path):
            self.stdout.write(f"Store directory does not exist: {store_path}")
            return

        pattern = os.path.join(store_path, 'silrec_db_*.dump')
        dump_files = sorted(glob.glob(pattern), key=os.path.getmtime)

        self.stdout.write(f"Found {len(dump_files)} dump files, keeping {keep}")

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
