# 1. Create a copy of the backup .sql file
cp silrec_v3_backup_01Apr2025.sql silrec_v3_backup_01Apr2025-OWNER-DEV.sql

# 2. 
Comment-out 3 lines

--CREATE SCHEMA public.

--ALTER SCHEMA public.OWNER TO dev;

--COMMENT ON SCHEMA public.IS 'Proposed';

# 3.
Change owner from postgres to <new_role>
a. Open backup .sql file in vi
b. :%s/OWNER TO postgres/OWNER TO dev/g

---------------------
# 4. Create the DB and Role (from file)
psql -h localhost -p 5432 -U postgres -f silrec_test2.sql

# 5. Try connecting
psql -h localhost -p 5432 -U dev -d silrec_test2

# restore to new DB
psql -h localhost -p 5432 -U dev silrec_test2 < ../tmp/silrec_v3_backup_01Apr2025-OWNER-DEV.sql

psql -h localhost -p 5432 -U dev -b -L log.txt silrec_test2 < ../tmp/silrec_v3_backup_01Apr2025-OWNER-DEV.sql

----------------------

# 6. Test Trigger function
psql -h localhost -p 5432 -U dev -d silrec_test2
silrec_test2=> select year_last_cut from cohort where cohort_id=116012;
 year_last_cut 
---------------
          1965
(1 row)

silrec_test2=> select count(*) from cohort_jn;
 count 
-------
     0
(1 row)

silrec_test2=> UPDATE cohort SET year_last_cut=1960 WHERE cohort_id=116012;
UPDATE 1
silrec_test2=> select count(*) from cohort_jn;
 count 
-------
     1
(1 row)

---------------

# Join SQL Example







