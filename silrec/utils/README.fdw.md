
1. Install the postgres_fdw extension:
\c silrec_test2
CREATE EXTENSION postgres_fdw;


2. Create a foreign server: 
CREATE SERVER localhost
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', port '5432', dbname 'silrec_test1');


3. Create a user mapping:
CREATE USER MAPPING FOR dev
SERVER localhost
OPTIONS (user 'my_username', password 'my_passwd');

DROP USER MAPPING FOR dev SERVER localhost;

CREATE USER MAPPING FOR postgres
SERVER localhost
OPTIONS (user 'postgres', password 'postgres');

4. Either create foreign table individually or get all 
a: ALL into schema IRIS

CREATE SCHEMA iris;

IMPORT FOREIGN SCHEMA public
FROM SERVER localhost
INTO iris;
            
b. 
CREATE FOREIGN TABLE foreign_cohort (
    cohort_id SERIAL PRIMARY KEY,
    obj_code VARCHAR(20),
    op_id INTEGER,
    year_last_cut INTEGER
)
SERVER localhost
OPTIONS (schema_name 'public', table_name 'cohort');


5. Set Search Path so other SCHEMA can be viewed (by default only PUBLIC is viewable)
SET search_path = iris, public;

6. Create a JOIN query and test

SELECT public.cohort.cohort_id FROM public.cohort
LEFT JOIN iris.cohort
USING (obj_code)
WHERE public.cohort.obj_code LIKE 'J-CROP%';
