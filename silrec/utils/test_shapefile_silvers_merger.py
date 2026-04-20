import os
import pickle
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'silrec.settings')
django.setup()

import geopandas as gpd
from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger
from silrec.utils.create_temp_tables import drop_prod_tables_django
from silrec.components.proposals.models import Proposal
from silrec.components.forest_blocks.models import Polygon, Cohort, AssignChtToPly

import subprocess
import logging

logger = logging.getLogger(__name__)

BASELINE_FILE = 'baseline_result.pkl'
DUMP_FILE = 'silrec_3tables_14Mar2026.dump'
SHAPEFILE = 'silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp'
PROPOSAL_ID = 1
THRESHOLD = 5
USER_ID = 1


def setup_database():
    drop_prod_tables_django()
    subprocess.run(
        ['pg_restore', '-h', 'localhost', '-p', '5432', '-U', 'dev', '-d', 'silrec_test3', DUMP_FILE],
        env={'PGPASSWORD': 'dev123'},
        check=True,
        capture_output=True
    )


def run_processing():
    gdf_shp = gpd.read_file(SHAPEFILE)
    ssm = ShapefileSliversMerger(
        proposal_id=PROPOSAL_ID,
        gdf_shpfile=gdf_shp,
        threshold=THRESHOLD,
        user_id=USER_ID
    )
    list_state = ssm.create_gdf()
    return list_state[0]['GDF_RESULT_COMBINED']


def save_baseline(result=None, force=False):
    if result is None:
        setup_database()
        result = run_processing()

    if os.path.exists(BASELINE_FILE) and not force:
        print(f"Baseline already exists: {BASELINE_FILE}")
        print("Use force=True to overwrite")
        return False

    with open(BASELINE_FILE, 'wb') as f:
        pickle.dump(result, f)

    print(f"Baseline saved: {len(result)} rows, {len(set(result['poly_id_new'].dropna().astype(int)))} unique poly_id_new")
    return True


def load_baseline():
    with open(BASELINE_FILE, 'rb') as f:
        return pickle.load(f)


def verify_baseline(result=None, verbose=True):
    result = result or run_processing()
    baseline = load_baseline()

    checks = {
        'row_count': len(baseline) == len(result),
        'poly_id_new': set(baseline['poly_id_new'].dropna().astype(int)) == set(result['poly_id_new'].dropna().astype(int)),
        'polygon_id': set(baseline['polygon_id'].dropna().astype(int)) == set(result['polygon_id'].dropna().astype(int)),
        'cohort_id': set(baseline['cohort_id'].dropna().astype(int)) == set(result['cohort_id'].dropna().astype(int)),
        'cht_id_cur': set(baseline['cht_id_cur'].dropna().astype(int)) == set(result['cht_id_cur'].dropna().astype(int)),
        'cht_id_new': set(baseline['cht_id_new'].dropna().astype(int)) == set(result['cht_id_new'].dropna().astype(int)),
        'cht_type': set(baseline['cht_type'].dropna()) == set(result['cht_type'].dropna()),
        'poly_type': set(baseline['poly_type'].dropna()) == set(result['poly_type'].dropna()),
        'area_ha': set((baseline['area_ha'] * 100).round().astype(int)) == set((result['area_ha'] * 100).round().astype(int)),
    }

    all_passed = all(checks.values())

    if verbose:
        print(f"Baseline rows: {len(baseline)}")
        print(f"Result rows: {len(result)}")
        print("Checks:")
        for name, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {name}: {status}")

    if all_passed:
        print("\n✓ ALL CHECKS PASSED")
    else:
        print("\n✗ SOME CHECKS FAILED")

    return all_passed


def run_full_test():
    print("=" * 60)
    print("ShapefileSliversMerger Baseline Test")
    print("=" * 60)

    setup_database()
    result = run_processing()

    if not os.path.exists(BASELINE_FILE):
        print("\nNo baseline found. Saving current result as baseline...")
        save_baseline(result)
        return True

    return verify_baseline(result)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'save':
            setup_database()
            result = run_processing()
            save_baseline(result, force=True)
        elif cmd == 'verify':
            setup_database()
            result = run_processing()
            verify_baseline(result)
        elif cmd == 'force-save':
            setup_database()
            result = run_processing()
            save_baseline(result, force=True)
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python test_shapefile_silvers_merger.py [save|verify|force-save]")
    else:
        run_full_test()
