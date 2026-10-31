from django.core.management.base import BaseCommand

from silrec.components.main.package_status import (
    collect_npm_status,
    collect_package_status,
    save_cache,
)


class Command(BaseCommand):
    help = (
        'Scan installed Python packages and frontend Node.js/Vue.js modules for '
        'outdated versions and known vulnerabilities, then cache the result for '
        'the Package Status admin page.'
    )

    def handle(self, *args, **options):
        self.stdout.write('Scanning Python packages (pip + OSV)...')
        data = collect_package_status()
        self.stdout.write('Scanning Node.js modules (npm registry + OSV)...')
        npm = collect_npm_status()
        if npm:
            data['npm_packages'] = npm['packages']
            data['npm_total_packages'] = npm['total_packages']
            data['npm_outdated_count'] = npm['outdated_count']
            data['npm_vulnerable_count'] = npm['vulnerable_count']
        else:
            data['npm_packages'] = []
            data['npm_total_packages'] = 0
            data['npm_outdated_count'] = 0
            data['npm_vulnerable_count'] = 0
        save_cache(data)
        self.stdout.write(
            self.style.SUCCESS(
                'Scan complete — Python: {} packages, {} outdated, {} vulnerable. '
                'Node.js: {} modules, {} outdated, {} vulnerable.'.format(
                    data['total_packages'],
                    data['outdated_count'],
                    data['vulnerable_count'],
                    data['npm_total_packages'],
                    data['npm_outdated_count'],
                    data['npm_vulnerable_count'],
                )
            )
        )
