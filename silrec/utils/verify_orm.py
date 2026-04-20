import os, pickle, sys, logging
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'silrec.settings')
import django; django.setup()

import geopandas as gpd
from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger
from silrec.utils.create_temp_tables import drop_prod_tables_django
import subprocess as sp

gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
drop_prod_tables_django()
sp.run(['pg_restore', '-h', 'localhost', '-p', '5432', '-U', 'dev', '-d', 'silrec_test3', 'silrec_3tables_14Mar2026.dump'], env={'PGPASSWORD': 'dev123'}, check=True, capture_output=True)

ssm = ShapefileSliversMerger(proposal_id=1, gdf_shpfile=gdf_shp, threshold=5, user_id=1)
list_state = ssm.create_gdf()
result = list_state[0]['GDF_RESULT_COMBINED']

with open('baseline_result.pkl', 'rb') as f:
    baseline = pickle.load(f)

b_ids = set(baseline['poly_id_new'].dropna().astype(int))
r_ids = set(result['poly_id_new'].dropna().astype(int))
msg = "SUCCESS" if b_ids == r_ids else "FAILED"
print(f"Django ORM verified: {msg} ({len(r_ids)} IDs)")
sys.exit(0 if b_ids == r_ids else 1)