from django.core.management.base import BaseCommand
from silrec.components.proposals.models import RequestMetrics, AuditLog
from silrec.components.forest_blocks.models import Polygon, Cohort, AssignChtToPly

class Command(BaseCommand):
    help = 'Clean up orphaned records from failed processing operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without deleting records',
        )
        parser.add_argument(
            '--proposal-id',
            type=int,
            help='Clean up only for a specific proposal',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        proposal_id = options['proposal_id']

        self.stdout.write(f"Running {'DRY RUN' if dry_run else 'ACTUAL'} cleanup")

        # Find orphaned records
        orphaned_polygons = []

        if proposal_id:
            # Find polygons without assignments or with closed assignments but no current cohort
            from django.db.models import Q, Exists, OuterRef

            # Polygons with no assignments at all
            polygons_no_assign = Polygon.objects.filter(
                proposal_id=proposal_id
            ).annotate(
                has_assign=Exists(
                    AssignChtToPly.objects.filter(polygon=OuterRef('polygon_id'))
                )
            ).filter(has_assign=False)

            orphaned_polygons.extend(polygons_no_assign)

            # Polygons with assignments but all are closed and no current one
            polygons_closed = Polygon.objects.filter(
                proposal_id=proposal_id
            ).annotate(
                has_current=Exists(
                    AssignChtToPly.objects.filter(
                        polygon=OuterRef('polygon_id'),
                        status_current=True
                    )
                )
            ).filter(has_current=False).exclude(
                polygon_id__in=[p.polygon_id for p in polygons_no_assign]
            )

            orphaned_polygons.extend(polygons_closed)

        self.stdout.write(f"Found {len(orphaned_polygons)} orphaned polygons")

        if not dry_run:
            for polygon in orphaned_polygons:
                self.stdout.write(f"  Deleting polygon {polygon.polygon_id}: {polygon.name}")
                polygon.delete()

            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {len(orphaned_polygons)} orphaned polygons"))

