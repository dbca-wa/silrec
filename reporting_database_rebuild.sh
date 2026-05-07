#!/bin/bash

echo "Running database collection and merge into new database for reporting.";

if [[ $TEMPORARY_SILREC_DATABASE == 'silrec_prod' || $TEMPORARY_SILREC_DATABASE == 'silrec_uat' ]]; then
        echo "ERROR: silrec_prod|silrec_uat can not be a TEMPORARY Database";
        exit;
fi

echo "Dump Core Production Tables";
PGPASSWORD="$PRODUCTION_LEDGER_PASSWORD" pg_dump -t 'accounts_emailuser' -t 'basket_basket' -t 'basket_line' -t 'order_order' -t 'order_line' -t 'address_country' -t 'payments_bpaytransaction' -t 'payments_bpointtransaction' -t 'payments_cashtransaction' -t 'payments_invoice' -t 'accounts_organisation' -t 'accounts_organisationaddress' --file /dbdumps/ledger_core_prod.sql --format=custom --host $PRODUCTION_LEDGER_HOST --dbname $PRODUCTION_LEDGER_DATABASE --username $PRODUCTION_LEDGER_USERNAME

echo "Dump Core Disturbance Production Tables";
PGPASSWORD="$PRODUCTION_LEDGER_PASSWORD" pg_dump -t 'disturbance_*' --file /dbdumps/disturbance_core_prod.sql --format=custom --host $PRODUCTION_LEDGER_HOST --dbname $PRODUCTION_LEDGER_DATABASE --username $PRODUCTION_LEDGER_USERNAME

# DROP All TABLES IN DAILY DB
for I in $(psql "host=$TEMPORARY_LEDGER_HOST port=5432 dbname=$TEMPORARY_LEDGER_DATABASE user=$TEMPORARY_LEDGER_USERNAME password=$TEMPORARY_LEDGER_PASSWORD sslmode=require" -c "SELECT tablename FROM pg_tables where tablename not like 'pg\_%' and tablename not like 'sql\_%';" -t);
  do
  echo " drop table $I CASCADE; ";
  psql "host=$TEMPORARY_LEDGER_HOST port=5432 dbname=$TEMPORARY_LEDGER_DATABASE user=$TEMPORARY_LEDGER_USERNAME password=$TEMPORARY_LEDGER_PASSWORD sslmode=require" -c "drop table $I CASCADE;" -t
done

# IMPORT LEDGER PROD DATABASE INTO REPORTING 
echo "Importing Ledger Core prod into reporting database";
PGSSLMODE=require PGPASSWORD="$TEMPORARY_LEDGER_PASSWORD"  pg_restore  --host=$TEMPORARY_LEDGER_HOST --dbname=$TEMPORARY_LEDGER_DATABASE --username=$TEMPORARY_LEDGER_USERNAME /dbdumps/ledger_core_prod.sql

# IMPORT WLC 
echo "Importing Disturbance Core prod into reporting database";
PGSSLMODE=require PGPASSWORD="$TEMPORARY_LEDGER_PASSWORD"  pg_restore  --host=$TEMPORARY_LEDGER_HOST --dbname=$TEMPORARY_LEDGER_DATABASE --username=$TEMPORARY_LEDGER_USERNAME /dbdumps/disturbance_core_prod.sql

# GRANT SELECT to parkstay_ro account
for I in $(psql "host=$TEMPORARY_LEDGER_HOST port=5432 dbname=$TEMPORARY_LEDGER_DATABASE user=$TEMPORARY_LEDGER_USERNAME password=$TEMPORARY_LEDGER_PASSWORD sslmode=require" -c "SELECT tablename FROM pg_tables where tablename not like 'pg\_%' and tablename not like 'sql\_%' and tablename not like 'spatial\_%';" -t);
  do
  echo "GRANT SELECT ON $I TO das_ro;";
  psql "host=$TEMPORARY_LEDGER_HOST port=5432 dbname=$TEMPORARY_LEDGER_DATABASE user=$TEMPORARY_LEDGER_USERNAME password=$TEMPORARY_LEDGER_PASSWORD sslmode=require" -c "GRANT SELECT ON $I TO das_ro; " -t
done

# Monitor Timestamp
psql "host=$TEMPORARY_LEDGER_HOST port=5432 dbname=$TEMPORARY_LEDGER_DATABASE user=$TEMPORARY_LEDGER_USERNAME password=$TEMPORARY_LEDGER_PASSWORD sslmode=require" -c "CREATE TABLE report_tables_monitor (id, timestamp) AS SELECT 1, CURRENT_TIMESTAMP;" 

rm /dbdumps/ledger_core_prod.sql
rm /dbdumps/disturbance_core_prod.sql
