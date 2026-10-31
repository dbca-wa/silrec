from django.core.management.base import BaseCommand

from silrec.components.main.package_status import (
    collect_package_status,
    save_cache,
)


class Command(BaseCommand):
    help = (
        'Scan installed Python packages for outdated versions and known '
        'vulnerabilities, then cache the result for the Package Status admin page.'
    )

    def handle(self, *args, **options):
        self.stdout.write('Scanning installed packages (pip + OSV)...')
        data = collect_package_status()
        save_cache(data)
        self.stdout.write(
            self.style.SUCCESS(
                'Scan complete: {} packages, {} outdated, {} vulnerable.'.format(
                    data['total_packages'],
                    data['outdated_count'],
                    data['vulnerable_count'],
                )
            )
        )
