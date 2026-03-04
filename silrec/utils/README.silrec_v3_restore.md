03-Mar-2026

 1156  psql -h localhost -p 5432 -U postgres -W -f  ~/projects/docker_scripts/silrec_test3.sql
 1157  ./manage.py showmigrations
 1161  ./manage.py migrate lookups 0001 --fake
 1162  ./manage.py migrate forest_blocks 0001 --fake
 1164  ./manage.py migrate
 1157  ./manage.py showmigrations

 1166  ./manage.py loaddata silrec/fixtures/application_type.json silrec/fixtures/group.json silrec/fixtures/proposal_type.json silrec/fixtures/proposal.json silrec/fixtures/textsearch.json silrec/fixtures/shpfile_attrs_config.json silrec/fixtures/sqlreport.js

 ./manage.py shell_plus
 u=User.objects.create(first_name='jawaid', last_name='mushtaq', username='jawaidm', email='jawaid.mushtaq@dbca.wa.gov.au')
 u.set_password('jm')
 u.is_staff=True
 u.is_superuser=True
 u.save()

./manage.py dbshell
 ALTER TABLE polygon RENAME COLUMN compartmen TO compartment;

CREATE DATABASE silrec_orig_mpoly_silrec_v3_25Feb2026 WITH TEMPLATE silrec_test3;

# PG_DUMP
pg_dump -h localhost -p 5432 -U dev -d silrec_orig_mpoly_silrec_v3_25feb2026 -t silrec.assign_cht_to_ply -t silrec.cohort -t silrec.polygon -Fc -f silrec_test4_3tables_25Feb2026.dump

./manage shell_plus
import geopandas as gpd
from silrec.utils.plot_utils import plot_gdf, plot_multi, plot_overlay
from silrec.utils.shapefile_silvers_merger7 import ShapefileSliversMerger
from silrec.utils.helper import polygons_to_gdf
import json
from silrec.utils.create_temp_tables import create_temp_tables, drop_temp_tables_django, drop_prod_tables_django

gdf_shp_16 = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')

c=Cohort.objects.create(cohort_id=1, obj_code='NOTDEF', regen_method_id=' %')

ssm = ShapefileSliversMerger(gdf_shp_16, proposal_id=1, threshold=5, user_id=1)
list_state = ssm.create_gdf()
geom_data = ssm.set_proposal_data(list_state)

p = Proposal.objects.get(id=2)
p.geojson_data_processed = json.loads(list_state[0]['GDF_RESULT_COMBINED'].to_crs(settings.CRS).to_json())
p.geojson_data_hist = json.loads(list_state[0]['GDF_HIST'].to_crs(settings.CRS).to_json())
p.shapefile_json = json.loads(list_state[0]['GDF_SHP'].to_crs(settings.CRS).to_json())
p.geojson_data_processed_iters = geom_data
p.save()

plot_multi([list_state[0]['GDF_SHP'], list_state[0]['GDF_HIST'], list_state[0]['GDF_RESULT_COMBINED']])



------------------------------------------------------
26-Feb-2026

silrec_v3_backup_25Feb2026.sql


 1121  vi silrec_test2_25Feb2026.sql
 1129  vi ../tmp/silrec_v3_backup_25Feb2026.sql

       # Change:
       CREATE SCHEMA silrec;

       ALTER SCHEMA silrec OWNER TO dev;
       SET SEARCH_PATH=silrec;

       :%s/silrec_v3./silrec./g
       :%s/current_status/status_current/g
Search CHANGE
       updated_on timestamp without time zone
       created_on timestamp without time zone

# RENAME polygon.compartmen to polygon.compartment
ALTER TABLE polygon RENAME COLUMN compartmen TO compartment;
ALTER TABLE polygon RENAME COLUMN reason_clo TO reason_closed;

# Remove all lines in a file that contain a given string
 1130  sed -i '/silrec_user/d' ../tmp/silrec_v3_backup_25Feb2026.sql
 1131  sed -i '/silrec_mgr/d' ../tmp/silrec_v3_backup_25Feb2026.sql
 1132  sed -i '/johnm/d' ../tmp/silrec_v3_backup_25Feb2026.sql
 1133  sed -i '/shelleyp/d' ../tmp/silrec_v3_backup_25Feb2026.sql

 # Create the Database and grant permissions
 1139  psql -h localhost -p 5432 -U postgres -W -f  ~/projects/docker_scripts/silrec_test2.sql

 # Restore file to new Database 
 1140  psql -h localhost -p 5432 -U dev -d silrec_test2 -W -f ~/projects/tmp/silrec_v3_backup_25Feb2026.sql

 # Restore file to new Database - comment out lines with 'ALTER ... OWNER TO postgres'
 1224  cp ../tmp/silrec_v3_backup_25Feb2026.sql ../tmp/silrec_v3_backup_remove-OWNER-postgres_25Feb2026.sql                     
 1225  sed -i '/OWNER TO postgres/s/^/-- /' ../tmp/silrec_v3_backup_remove-OWNER-postgres_25Feb2026.sql                      
 1226  vi ../tmp/silrec_v3_backup_remove-OWNER-postgres_25Feb2026.sql                                                        

 1227  psql -h localhost -p 5432 -U postgres -W -f ../docker_scripts/silrec_test2.sql                                        
 1228  psql -h localhost -p 5432 -U dev -d silrec_test2 -W -f ~/projects/tmp/silrec_v3_backup_remove-OWNER-postgres_25Feb2026.sql         

-------------

Added Models 
    ObjectiveClassification
    TaskClassification

    and added the 
        obj_class_id to ObjectiveLkp
        task_class_id to TaskLkp

SQL
    (NOT NEEDED NOW - modified the silrec_v3_backup_25Feb2026.sql) ALTER TABLE assign_cht_to_ply RENAME COLUMN current_status TO status_current;
-------------

These migrations need to be faked
    Commented out reversion register lines in 
        forest_blocks.models.py
        lookups.models.py

    Commented out the TmpPolygon, TmpAssignChtToPly, TmpCohort models in forest_blocks.models.py



 1228  vi silrec/settings.py 
       comment-out apps
      	 'silrec.components.users',
    	 'silrec.components.forest_blocks',
         'silrec.components.lookups',
         'silrec.components.proposals',
         'silrec.components.main',

 1229  ./manage.py showmigrations
 1230  ./manage.py migrate

 1234  vi silrec/settings.py
       uncomment-out apps
      	 'silrec.components.users',
    	 'silrec.components.forest_blocks',
         'silrec.components.lookups',
         'silrec.components.proposals',
         'silrec.components.main',

 1233  ./manage.py showmigrations
 1236  ./manage.py migrate lookups 001 --fake
 1237  ./manage.py migrate forest_blocks 001 --fake
       ./manage.py migrate lookups
       ./manage.py migrate forest_blocks
 1237  ./manage.py migrate silrec
 1238  ./manage.py showmigrations

--------

 ./manage.py shell_plus
 u=User.objects.create(first_name='jawaid', last_name='mushtaq', username='jawaidm', email='jawaid.mushtaq@dbca.wa.gov.au')
 u.set_password('jm')
 u.is_staff=True 
 u.is_superuser=True
 u.save()

# Load Fixtures
./manage.py loaddata silrec/fixtures/application_type.json silrec/fixtures/group.json silrec/fixtures/proposal_type.json silrec/fixtures/proposal.json silrec/fixtures/textsearch.json silrec/fixtures/shpfile_attrs_config.json silrec/fixtures/sqlreport.json


./manage.py dbshell
 ALTER TABLE polygon RENAME COLUMN compartmen TO compartment;


CREATE DATABASE silrec_orig_mpoly_silrec_v3_25Feb2026 WITH TEMPLATE silrec_test2;

# PG_DUMP
pg_dump -h localhost -p 5432 -U dev -d silrec_orig_mpoly_silrec_v3_25feb2026 -t silrec.assign_cht_to_ply -t silrec.cohort -t silrec.polygon -Fc -f silrec_test4_3tables_25Feb2026.dump

# PG_RESTORE
PGPASSWORD='<password>' pg_restore -h localhost -p 5432 -U dev -d silrec_test2 silrec_test4_3tables_25Feb2026.dump -v

# settings.py - Add 'public' because Polygon.geom field saves a public.MultiPolygon in Postgres DB, and Django save() fails otherwise
DATABASES['default'].update(OPTIONS={'options': '-c search_path=silrec,public'})
-------
~/projects/silrec$ ./manage.py runserver 0.0.0.0:8001

cd silrec/frontend/silrec
~/projects/silrec/silrec/frontend/silrec$ npm run dev


