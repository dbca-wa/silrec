#!/usr/bin/env bash
# Usage: ./trim_pg_restore.sh <dbname> [backup.sql]
#
# Trims trailing spaces from all Django-managed CharField columns
# after restoring a pg_dump that used character(N) types.
#
# Steps:
#   1. Drops _jn audit triggers (prevents trigger errors during TRIM)
#   2. Drops FK constraints referencing PK tables being trimmed
#   3. Drops PK constraints (allows dedup of rows identical after trim)
#   4. Trims all varchar columns on Django-managed tables
#   5. Recreates PK and FK constraints
#   6. Recreates _jn triggers from the backup (if backup.sql provided)
#
# Requires PGPASSWORD env var or .pgpass for the dev user.
# Pass the original backup.sql to recreate _jn triggers automatically.

set -euo pipefail

DB="$1"
BACKUP="${2:-}"
PSQL="psql -h localhost -U dev -d $DB"

echo "=== 1. Drop _jn audit triggers ==="
$PSQL -c "
DO \$\$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT tgname, relname
    FROM pg_trigger t JOIN pg_class c ON t.tgrelid = c.oid
    WHERE t.tgname LIKE '%_jn_%' AND c.relnamespace = 'silrec'::regnamespace
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS %I ON silrec.%I;', r.tgname, r.relname);
  END LOOP;
END;
\$\$;
"

echo "=== 2. Drop FK constraints referencing PK tables ==="
$PSQL -c "
DO \$\$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT oid, conname, conrelid::regclass AS tbl
    FROM pg_constraint
    WHERE contype = 'f' AND connamespace = 'silrec'::regnamespace
      AND confrelid IN (
        'silrec.objective_lkp'::regclass,
        'silrec.organisation_lkp'::regclass,
        'silrec.regeneration_methods_lkp'::regclass,
        'silrec.task_lkp'::regclass,
        'silrec.compartments'::regclass,
        'silrec.reschedule_reasons_lkp'::regclass,
        'silrec.spatial_precision_lkp'::regclass,
        'silrec.species_api_lkp'::regclass,
        'silrec.tasks_att_lkp'::regclass,
        'silrec.treatment_status_lkp'::regclass
      )
  LOOP
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I;', r.tbl, r.conname);
  END LOOP;
END;
\$\$;
"

echo "=== 3. Drop PK constraints ==="
$PSQL -c "
ALTER TABLE ONLY silrec.objective_lkp DROP CONSTRAINT IF EXISTS \"obj_PK\" CASCADE;
ALTER TABLE ONLY silrec.organisation_lkp DROP CONSTRAINT IF EXISTS \"org_PK\" CASCADE;
ALTER TABLE ONLY silrec.regeneration_methods_lkp DROP CONSTRAINT IF EXISTS \"rm_PK\" CASCADE;
ALTER TABLE ONLY silrec.task_lkp DROP CONSTRAINT IF EXISTS \"tsk_PK\" CASCADE;
ALTER TABLE ONLY silrec.compartments DROP CONSTRAINT IF EXISTS \"cpt_PK\" CASCADE;
ALTER TABLE ONLY silrec.reschedule_reasons_lkp DROP CONSTRAINT IF EXISTS \"rr_PK\" CASCADE;
ALTER TABLE ONLY silrec.species_api_lkp DROP CONSTRAINT IF EXISTS \"asp_PK\" CASCADE;
ALTER TABLE ONLY silrec.spatial_precision_lkp DROP CONSTRAINT IF EXISTS \"sp_PK\" CASCADE;
ALTER TABLE ONLY silrec.tasks_att_lkp DROP CONSTRAINT IF EXISTS \"tsk_att_PK\" CASCADE;
ALTER TABLE ONLY silrec.treatment_status_lkp DROP CONSTRAINT IF EXISTS \"ts_PK\" CASCADE;
"

echo "=== 4. Trim trailing spaces ==="
$PSQL -c "
DELETE FROM silrec.objective_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.objective_lkp GROUP BY TRIM(obj_code));
UPDATE ONLY silrec.objective_lkp SET obj_code = TRIM(obj_code);
DELETE FROM silrec.organisation_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.organisation_lkp GROUP BY TRIM(organisation));
UPDATE ONLY silrec.organisation_lkp SET organisation = TRIM(organisation);
DELETE FROM silrec.regeneration_methods_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.regeneration_methods_lkp GROUP BY TRIM(regen_method));
UPDATE ONLY silrec.regeneration_methods_lkp SET regen_method = TRIM(regen_method);
DELETE FROM silrec.task_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.task_lkp GROUP BY TRIM(task));
UPDATE ONLY silrec.task_lkp SET task = TRIM(task);
DELETE FROM silrec.compartments WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.compartments GROUP BY TRIM(compartment));
UPDATE ONLY silrec.compartments SET compartment = TRIM(compartment);
DELETE FROM silrec.reschedule_reasons_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.reschedule_reasons_lkp GROUP BY TRIM(rescheduled_reason));
UPDATE ONLY silrec.reschedule_reasons_lkp SET rescheduled_reason = TRIM(rescheduled_reason);
UPDATE ONLY silrec.spatial_precision_lkp SET precision_code = TRIM(precision_code);
DELETE FROM silrec.species_api_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.species_api_lkp GROUP BY TRIM(species));
UPDATE ONLY silrec.species_api_lkp SET species = TRIM(species);
DELETE FROM silrec.tasks_att_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.tasks_att_lkp GROUP BY TRIM(addition_attrib));
UPDATE ONLY silrec.tasks_att_lkp SET addition_attrib = TRIM(addition_attrib);
DELETE FROM silrec.treatment_status_lkp WHERE ctid NOT IN (SELECT min(ctid) FROM silrec.treatment_status_lkp GROUP BY TRIM(status));
UPDATE ONLY silrec.treatment_status_lkp SET status = TRIM(status);

-- Trim FK referencing columns (now safe - PKs already cleaned)
UPDATE ONLY silrec.prescription SET obj_code = TRIM(obj_code);
UPDATE ONLY silrec.prescription SET task = TRIM(task);
UPDATE ONLY silrec.prescription SET responsibility = TRIM(responsibility);
UPDATE ONLY silrec.cohort SET obj_code = TRIM(obj_code);
UPDATE ONLY silrec.cohort SET regen_method = TRIM(regen_method);
UPDATE ONLY silrec.cohort SET species = TRIM(species);
UPDATE ONLY silrec.assign_task_to_report SET task = TRIM(task);
UPDATE ONLY silrec.treatment SET task = TRIM(task);
UPDATE ONLY silrec.treatment SET organisation = TRIM(organisation);
UPDATE ONLY silrec.assign_obj_to_report SET obj_code = TRIM(obj_code);
UPDATE ONLY silrec.assign_category_to_task SET task = TRIM(task);
UPDATE ONLY silrec.task_category SET task = TRIM(task);
UPDATE ONLY silrec.polygon SET compartmen = TRIM(compartmen);
UPDATE ONLY silrec.polygon_old SET compartment = TRIM(compartment);
UPDATE ONLY silrec.polygon_old SET sp_code = TRIM(sp_code);
UPDATE ONLY silrec.polygon_prior_to_area_fix SET compartment = TRIM(compartment);
UPDATE ONLY silrec.polygon_prior_to_area_fix SET sp_code = TRIM(sp_code);
UPDATE ONLY silrec.polygon SET sp_code = TRIM(sp_code);

-- Trim all remaining non-PK varchar columns on Django-managed tables
DO \$\$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT table_schema, table_name, column_name
    FROM information_schema.columns
    WHERE data_type = 'character varying'
      AND table_schema = 'silrec'
      AND table_name NOT LIKE '%_jn'
      AND table_name NOT LIKE 'vw_%'
      AND table_name NOT IN (
        'polygon_da', 'polygon_mining_union',
        'thinning_cohort', 'thinning_presc', 'thinning_trtmnts',
        'cl_comp_2024_polys_cleared_mga2020_50_pl',
        'combined_silrec_2023', 'combined_silrec_2023_2',
        'fea_active_fmp25_region',
        'ba_sweep', 'ba_sweep_transfer', 'ba_sweep_version',
        'ba_transect', 'ba_transect_transfer', 'cell',
        'silrec_ply_2023', 'silrec_version', 'silrec_version_tracking',
        'silvic_plan_input', 'silviculturist_comment',
        'duplicates', 'missing_cohort',
        'fpc_harvest_tracker', 'split_unchanged_polygons',
        'assign_cht_to_ply_bckup_before_multi_split',
        'assign_cht_to_ply_delete', 'koom_processed',
        'task_classification'
      )
    ORDER BY table_name, ordinal_position
  LOOP
    BEGIN
      EXECUTE format('UPDATE ONLY %I.%I SET %I = TRIM(%I);',
        r.table_schema, r.table_name, r.column_name, r.column_name);
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'SKIP %.%: %', r.table_name, r.column_name, SQLERRM;
    END;
  END LOOP;
END;
\$\$;
"

echo "=== 5. Recreate PK constraints ==="
$PSQL -c "
ALTER TABLE ONLY silrec.objective_lkp ADD CONSTRAINT \"obj_PK\" PRIMARY KEY (obj_code);
ALTER TABLE ONLY silrec.organisation_lkp ADD CONSTRAINT \"org_PK\" PRIMARY KEY (organisation);
ALTER TABLE ONLY silrec.regeneration_methods_lkp ADD CONSTRAINT \"rm_PK\" PRIMARY KEY (regen_method);
ALTER TABLE ONLY silrec.task_lkp ADD CONSTRAINT \"tsk_PK\" PRIMARY KEY (task);
ALTER TABLE ONLY silrec.compartments ADD CONSTRAINT \"cpt_PK\" PRIMARY KEY (compartment);
ALTER TABLE ONLY silrec.reschedule_reasons_lkp ADD CONSTRAINT \"rr_PK\" PRIMARY KEY (rescheduled_reason);
ALTER TABLE ONLY silrec.species_api_lkp ADD CONSTRAINT \"asp_PK\" PRIMARY KEY (species);
ALTER TABLE ONLY silrec.spatial_precision_lkp ADD CONSTRAINT \"sp_PK\" PRIMARY KEY (precision_code);
ALTER TABLE ONLY silrec.tasks_att_lkp ADD CONSTRAINT \"tsk_att_PK\" PRIMARY KEY (addition_attrib);
ALTER TABLE ONLY silrec.treatment_status_lkp ADD CONSTRAINT \"ts_PK\" PRIMARY KEY (status);
"

echo "=== 6. Recreate FK constraints ==="
$PSQL -c "
ALTER TABLE ONLY silrec.cohort ADD CONSTRAINT cht_obj_FK FOREIGN KEY (obj_code) REFERENCES silrec.objective_lkp(obj_code);
ALTER TABLE ONLY silrec.cohort ADD CONSTRAINT cht_rm_FK FOREIGN KEY (regen_method) REFERENCES silrec.regeneration_methods_lkp(regen_method);
ALTER TABLE ONLY silrec.cohort ADD CONSTRAINT cht_species_FK FOREIGN KEY (species) REFERENCES silrec.species_api_lkp(species);
ALTER TABLE ONLY silrec.prescription ADD CONSTRAINT prscn_obj_FK FOREIGN KEY (obj_code) REFERENCES silrec.objective_lkp(obj_code);
ALTER TABLE ONLY silrec.prescription ADD CONSTRAINT prscn_tsk_FK FOREIGN KEY (task) REFERENCES silrec.task_lkp(task);
ALTER TABLE ONLY silrec.prescription ADD CONSTRAINT prsn_org_FK FOREIGN KEY (responsibility) REFERENCES silrec.organisation_lkp(organisation);
ALTER TABLE ONLY silrec.assign_task_to_report ADD CONSTRAINT tsk2trpt_tsk_FK FOREIGN KEY (task) REFERENCES silrec.task_lkp(task);
ALTER TABLE ONLY silrec.treatment ADD CONSTRAINT trt_tsk_FK FOREIGN KEY (task) REFERENCES silrec.task_lkp(task);
ALTER TABLE ONLY silrec.treatment ADD CONSTRAINT trt_org_FK FOREIGN KEY (organisation) REFERENCES silrec.organisation_lkp(organisation);
ALTER TABLE ONLY silrec.assign_obj_to_report ADD CONSTRAINT obj2orpt_obj_FK FOREIGN KEY (obj_code) REFERENCES silrec.objective_lkp(obj_code);
ALTER TABLE ONLY silrec.assign_category_to_task ADD CONSTRAINT task2cat_task_FK FOREIGN KEY (task) REFERENCES silrec.task_lkp(task);
ALTER TABLE ONLY silrec.polygon ADD CONSTRAINT ply_cpt_FK FOREIGN KEY (compartmen) REFERENCES silrec.compartments(compartment);
ALTER TABLE ONLY silrec.polygon ADD CONSTRAINT ply_sp_FK FOREIGN KEY (sp_code) REFERENCES silrec.spatial_precision_lkp(precision_code);
"

if [ -n "$BACKUP" ]; then
    echo "=== 7. Recreate _jn triggers from backup ==="
    python3 -c "
import re, sys
content = open('$BACKUP').read()
triggers = []
for m in re.finditer(r'CREATE\s+TRIGGER\s+(\S+).*?ON\s+(\S+)\s+FOR\s+EACH\s+ROW\s+EXECUTE\s+FUNCTION\s+(\S+\(\))', content, re.DOTALL):
    if 'jn_func' in m.group(3):
        triggers.append(m.group(0))
with open('/tmp/trim_recreate_triggers.sql', 'w') as f:
    f.write('BEGIN;\n')
    for t in triggers:
        f.write(t + ';\n')
    f.write('COMMIT;\n')
print(f'{len(triggers)} triggers to recreate')
" 2>&1
    $PSQL -f /tmp/trim_recreate_triggers.sql 2>&1 | tail -3
fi

echo "=== Done ==="
