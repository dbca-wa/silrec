"""Package status scanning for the Silrec admin.

Collects the Python packages installed in this project's environment and
reports, for each, the installed version, the latest version available on
PyPI, and known vulnerabilities from the OSV database (the same source used
by ``pip-audit``). Results are cached to a JSON file so the admin page loads
quickly; re-scan via the "Scan now" button or the ``scan_package_status``
management command.
"""

import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse

CACHE_FILENAME = 'package_status_cache.json'
OSV_BATCH_URL = 'https://api.osv.dev/v1/querybatch'
OSV_VULN_URL = 'https://api.osv.dev/v1/vulns/'
OSV_CHUNK_SIZE = 100

SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'unknown']

# Packages whose max installable version is bounded by a system library (not
# resolvable by pip) — excluded from the max-version resolution.
SYSTEM_BOUND_PACKAGES = {'gdal', 'fiona', 'pyproj', 'pyogrio', 'rasterio'}


def cache_path():
    return os.path.join(settings.BASE_DIR, CACHE_FILENAME)


def _installed_packages():
    """Return {name: version} for every installed distribution."""
    from importlib import metadata

    pkgs = {}
    for dist in metadata.distributions():
        # Skip vendored copies (e.g. setuptools/_vendor/*) which
        # importlib.metadata also surfaces and which shadow the real
        # installed packages.
        path = str(getattr(dist, '_path', '') or '')
        if '_vendor' in path:
            continue
        name = (dist.metadata.get('Name') or '').strip()
        version = dist.version or ''
        if name and version:
            pkgs[name] = version
    return pkgs


def _pip_outdated():
    """Return {name_lower: latest_version} for packages with a newer PyPI release."""
    try:
        out = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if out.returncode != 0:
            return {}
        return {
            row['name'].lower(): row['latest_version']
            for row in json.loads(out.stdout)
        }
    except Exception:
        return {}


def _pip_max_versions(outdated_names):
    """Resolve the max installable version for each outdated package.

    Uses pip's resolver in dry-run mode to find the highest version of each
    package that is compatible with the currently installed environment
    (and the other upgraded packages). Returns {name_lower: version}.
    """
    names = [n for n in outdated_names if n.lower() not in SYSTEM_BOUND_PACKAGES]
    if not names:
        return {}

    fd, report_file = tempfile.mkstemp(suffix='.json', prefix='pip_max_report_')
    os.close(fd)
    try:
        result = subprocess.run(
            [
                sys.executable, '-m', 'pip', 'install',
                '--dry-run', '--upgrade', '--upgrade-strategy', 'only-if-needed',
                '--only-binary', ':all:', '--report', report_file,
            ] + names,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            return {}
        with open(report_file) as f:
            report = json.load(f)
        max_versions = {}
        for item in report.get('install', []):
            md = item.get('metadata') or {}
            name = md.get('name')
            version = md.get('version')
            if name and version:
                max_versions[name.lower()] = version
        return max_versions
    except Exception:
        return {}
    finally:
        try:
            os.remove(report_file)
        except OSError:
            pass


def _fetch_one_vuln(vid):
    url = OSV_VULN_URL + urllib.parse.quote(vid, safe='')
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return vid, json.load(resp)
    except Exception:
        return vid, None


def _fetch_vuln_details(ids):
    result = {}
    if not ids:
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for vid, detail in executor.map(_fetch_one_vuln, ids):
            if detail:
                result[vid] = detail
    return result


def _osv_vulnerabilities(packages, ecosystem='PyPI'):
    """Query OSV for vulnerabilities keyed by package name (full details).

    The batch endpoint only returns vulnerability ids, so full
    severity/summary details are fetched per-vulnerability, concurrently.
    """
    names = list(packages.keys())
    queries = [
        {'package': {'name': name, 'ecosystem': ecosystem}, 'version': packages[name]}
        for name in names
    ]

    vuln_ids = {}  # name -> [id, ...]
    for i in range(0, len(queries), OSV_CHUNK_SIZE):
        chunk_names = names[i:i + OSV_CHUNK_SIZE]
        chunk_queries = queries[i:i + OSV_CHUNK_SIZE]
        payload = json.dumps({'queries': chunk_queries}).encode('utf-8')
        req = urllib.request.Request(
            OSV_BATCH_URL,
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.load(resp)
        except Exception:
            continue
        results = data.get('results', [])
        for name, res in zip(chunk_names, results):
            ids = [v.get('id') for v in res.get('vulns', []) if v.get('id')]
            if ids:
                vuln_ids[name] = ids

    all_ids = sorted({vid for ids in vuln_ids.values() for vid in ids})
    details = _fetch_vuln_details(all_ids)

    result = {}
    for name, ids in vuln_ids.items():
        result[name] = [details[vid] for vid in ids if vid in details]
    return result


def _severity(vuln):
    """Best-effort severity string for an OSV vulnerability entry."""
    ds = vuln.get('database_specific') or {}
    raw = str(ds.get('severity') or '').upper()
    if raw:
        if 'CRITICAL' in raw:
            return 'critical'
        if 'HIGH' in raw:
            return 'high'
        if 'MODERATE' in raw or 'MEDIUM' in raw:
            return 'medium'
        if 'LOW' in raw:
            return 'low'

    for item in vuln.get('severity') or []:
        try:
            score = float(str(item.get('score', '')).split('/')[0])
        except (TypeError, ValueError):
            continue
        if score >= 9.0:
            return 'critical'
        if score >= 7.0:
            return 'high'
        if score >= 4.0:
            return 'medium'
        return 'low'

    try:
        score = float((ds.get('cvss') or {}).get('score'))
    except (TypeError, ValueError):
        return 'unknown'
    if score >= 9.0:
        return 'critical'
    if score >= 7.0:
        return 'high'
    if score >= 4.0:
        return 'medium'
    return 'low'


def _frontend_dir():
    """Directory containing the frontend package.json / package-lock.json."""
    return os.path.join(settings.BASE_DIR, 'silrec', 'frontend', 'silrec')


def _npm_packages():
    """Return {name: {version, declared, type}} for the frontend's npm deps.

    Reads package.json (declared ranges + dep/devDep type) and resolves the
    actually-installed version from package-lock.json.
    """
    pkg_path = os.path.join(_frontend_dir(), 'package.json')
    lock_path = os.path.join(_frontend_dir(), 'package-lock.json')
    if not os.path.exists(pkg_path):
        return {}

    try:
        with open(pkg_path) as f:
            pkg = json.load(f)
    except Exception:
        return {}

    declared = {}
    for dep_type, section in (
        ('dependency', 'dependencies'),
        ('devDependency', 'devDependencies'),
    ):
        for name, spec in (pkg.get(section) or {}).items():
            declared[name] = {'declared': spec, 'type': dep_type}

    resolved = {}
    try:
        with open(lock_path) as f:
            lock = json.load(f)
        for path, info in (lock.get('packages') or {}).items():
            if not path.startswith('node_modules/'):
                continue
            name = path[len('node_modules/'):]
            # skip nested dependencies and the root entry
            if not name or '/node_modules/' in name:
                continue
            resolved[name] = info.get('version')
    except Exception:
        resolved = {}

    result = {}
    for name, meta in declared.items():
        version = resolved.get(name) or str(meta['declared']).lstrip('^~><= ')
        result[name] = {
            'version': version,
            'declared': meta['declared'],
            'type': meta['type'],
        }
    return result


def _npm_latest(names):
    """Return {name: latest_version} from the npm registry (concurrent)."""
    def _fetch(name):
        url = 'https://registry.npmjs.org/' + urllib.parse.quote(name, safe='')
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.load(resp)
            return name, (data.get('dist-tags') or {}).get('latest')
        except Exception:
            return name, None

    result = {}
    if not names:
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        for name, latest in executor.map(_fetch, names):
            if latest:
                result[name] = latest
    return result


def collect_npm_status():
    """Scan the frontend's Node.js/Vue.js dependencies (package.json + lock)."""
    pkgs = _npm_packages()
    if not pkgs:
        return None

    versions = {name: meta['version'] for name, meta in pkgs.items()}
    latest = _npm_latest(list(pkgs.keys()))
    vulnerabilities = _osv_vulnerabilities(versions, ecosystem='npm')

    packages = []
    for name in sorted(pkgs, key=str.lower):
        meta = pkgs[name]
        version = meta['version']
        latest_v = latest.get(name)
        pkg_vulns = vulnerabilities.get(name, [])

        severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        vuln_details = []
        for vuln in pkg_vulns:
            sev = _severity(vuln)
            severity[sev] += 1
            vuln_details.append({
                'id': vuln.get('id', ''),
                'severity': sev,
                'summary': (vuln.get('summary') or '')[:200],
            })
        vuln_details.sort(key=lambda d: SEVERITY_ORDER.index(d['severity']))

        outdated = bool(latest_v and version != latest_v)
        packages.append({
            'name': name,
            'type': meta['type'],
            'version': version,
            'declared': meta['declared'],
            'latest_version': latest_v,
            'outdated': outdated,
            'vuln_count': len(pkg_vulns),
            'severity': severity,
            'vulns': vuln_details,
            'needs_attention': outdated or len(pkg_vulns) > 0,
        })

    packages.sort(
        key=lambda p: (
            -p['vuln_count'],
            -p['severity']['critical'],
            -p['severity']['high'],
            -int(p['outdated']),
            p['name'].lower(),
        )
    )

    return {
        'total_packages': len(packages),
        'outdated_count': sum(1 for p in packages if p['outdated']),
        'vulnerable_count': sum(1 for p in packages if p['vuln_count']),
        'packages': packages,
    }


def collect_package_status():
    """Scan installed packages and return the full status dict."""
    installed = _installed_packages()
    outdated = _pip_outdated()
    vulnerabilities = _osv_vulnerabilities(installed)
    max_versions = _pip_max_versions(list(outdated.keys()))

    packages = []
    for name in sorted(installed, key=str.lower):
        version = installed[name]
        latest = outdated.get(name.lower())
        pkg_vulns = vulnerabilities.get(name, [])

        severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        vuln_details = []
        for vuln in pkg_vulns:
            sev = _severity(vuln)
            severity[sev] += 1
            vuln_details.append({
                'id': vuln.get('id', ''),
                'severity': sev,
                'summary': (vuln.get('summary') or '')[:200],
            })
        vuln_details.sort(
            key=lambda d: SEVERITY_ORDER.index(d['severity'])
        )

        packages.append({
            'name': name,
            'version': version,
            'latest_version': latest,
            'max_version': max_versions.get(name.lower()),
            'outdated': latest is not None,
            'vuln_count': len(pkg_vulns),
            'severity': severity,
            'vulns': vuln_details,
            'needs_attention': latest is not None or len(pkg_vulns) > 0,
        })

    # Vulnerable / outdated first, then alphabetically.
    packages.sort(
        key=lambda p: (
            -p['vuln_count'],
            -p['severity']['critical'],
            -p['severity']['high'],
            -int(p['outdated']),
            p['name'].lower(),
        )
    )

    return {
        'scanned_at': datetime.now().isoformat(timespec='seconds'),
        'total_packages': len(packages),
        'outdated_count': sum(1 for p in packages if p['outdated']),
        'vulnerable_count': sum(1 for p in packages if p['vuln_count']),
        'packages': packages,
    }


def save_cache(data):
    tmp = cache_path() + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f)
    os.replace(tmp, cache_path())


def load_cache():
    try:
        with open(cache_path()) as f:
            return json.load(f)
    except Exception:
        return None


def package_status_view(request):
    if request.method == 'POST':
        try:
            data = collect_package_status()
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
            messages.success(
                request,
                'Scan complete — Python: {} outdated, {} vulnerable. '
                'Node.js: {} outdated, {} vulnerable.'.format(
                    data['outdated_count'], data['vulnerable_count'],
                    data['npm_outdated_count'], data['npm_vulnerable_count'],
                ),
            )
        except Exception as exc:
            messages.error(request, 'Scan failed: {}'.format(exc))
        return HttpResponseRedirect(reverse('admin_package_status'))

    data = load_cache()
    if data is not None:
        data.setdefault('npm_packages', [])
        data.setdefault('npm_total_packages', 0)
        data.setdefault('npm_outdated_count', 0)
        data.setdefault('npm_vulnerable_count', 0)
    context = dict(admin.site.each_context(request))
    context.update({
        'title': 'Package Status',
        'data': data,
        'csrf_token': get_token(request),
    })
    return render(request, 'admin/package_status.html', context)
