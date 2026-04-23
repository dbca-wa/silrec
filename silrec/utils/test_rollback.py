import geopandas as gpd
from django.db import transaction, connection
from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger
from silrec.utils.create_temp_tables import drop_prod_tables_django
import subprocess
from subprocess import CalledProcessError
import os
import uuid
from datetime import datetime

# In-memory store for pending savepoints (for testing)
# In production, store in Proposal model or separate table
PENDING_SAVEPOINTS = {}

# Tables that get modified by create_gdf()
AFFECTED_TABLES = ['polygon', 'cohort', 'assign_cht_to_ply', 'treatment', 'treatment_xtra']

# Dump file storage directory
DUMP_DIR = '/tmp/silrec_dumps'


def ensure_dump_dir():
    """Ensure dump directory exists"""
    os.makedirs(DUMP_DIR, exist_ok=True)


def get_baseline_counts(proposal_id):
    """Get baseline table counts for a proposal"""
    counts = get_table_counts_dict()
    counts['proposal_id'] = proposal_id
    counts['timestamp'] = datetime.now().isoformat()
    return counts


def run_phase1_process(proposal_id, user_id):
    """
    Phase 1: Create baseline dump, run processing, return results.
    
    This corresponds to API endpoint that starts the processing.
    
    Returns:
        dict with:
            - transaction_id: unique ID to reference this operation
            - list_state: processing results
            - baseline_counts: table counts before processing (for display)
            - dump_file: path to baseline dump
    """
    ensure_dump_dir()
    
    # Generate unique transaction ID
    transaction_id = f"{proposal_id}_{uuid.uuid4().hex[:8]}"
    dump_file = os.path.join(DUMP_DIR, f'{transaction_id}.dump')
    
    # Get baseline counts BEFORE processing
    baseline_counts = get_baseline_counts(proposal_id)
    
    # Dump affected tables BEFORE processing (creates baseline backup)
    affected_for_dump = [{'table': t} for t in AFFECTED_TABLES]
    print(f"Phase 1: Dumping baseline to {dump_file}")
    dump_affected_tables(affected_for_dump, dump_file)
    
    # Run processing
    print(f"Phase 1: Running processing for proposal {proposal_id}")
    ssm = ShapefileSliversMerger(proposal_id=proposal_id, threshold=5, user_id=user_id)
    list_state = ssm.create_gdf()
    
    # Get counts after processing
    after_counts = get_table_counts_dict()
    affected = get_affected_tables(baseline_counts, after_counts)
    
    # Store pending operation
    PENDING_SAVEPOINTS[transaction_id] = {
        'proposal_id': proposal_id,
        'dump_file': dump_file,
        'baseline_counts': baseline_counts,
        'after_counts': after_counts,
        'affected_tables': affected,
        'timestamp': datetime.now().isoformat(),
    }
    
    print(f"Phase 1 complete. Transaction ID: {transaction_id}")
    print(f"Tables changed: {[t['table'] for t in affected]}")
    print(f"Call run_phase2_rollback('{transaction_id}') to rollback or run_phase2_accept('{transaction_id}') to commit")
    
    return {
        'transaction_id': transaction_id,
        'list_state': list_state,
        'baseline_counts': baseline_counts,
        'after_counts': after_counts,
        'dump_file': dump_file,
        'affected_tables': affected,
    }


def run_phase2_rollback(transaction_id):
    """
    Phase 2a: Restore baseline dump (rollback).
    
    This corresponds to API endpoint for "Reject/Discard" button.
    
    Args:
        transaction_id: from Phase 1 response
        
    Returns:
        dict with success status and message
    """
    if transaction_id not in PENDING_SAVEPOINTS:
        return {'success': False, 'error': f'Transaction {transaction_id} not found'}
    
    pending = PENDING_SAVEPOINTS[transaction_id]
    dump_file = pending['dump_file']
    baseline_counts = pending['baseline_counts']
    
    if not os.path.exists(dump_file):
        return {'success': False, 'error': f'Dump file {dump_file} not found'}
    
    print(f"Phase 2: Rolling back {transaction_id}")
    print(f"Restoring from: {dump_file}")
    
    # Restore from baseline dump
    restore_affected_tables(AFFECTED_TABLES, dump_file)
    
    # Verify restoration
    final_counts = get_table_counts_dict()
    success = True
    for table in AFFECTED_TABLES:
        baseline = baseline_counts.get(table, 0)
        final = final_counts.get(table, 0)
        if baseline != final:
            success = False
            print(f"FAILED: {table} baseline={baseline}, final={final}")
    
    # Cleanup
    if os.path.exists(dump_file):
        os.remove(dump_file)
    del PENDING_SAVEPOINTS[transaction_id]
    
    if success:
        print(f"Rollback complete: {transaction_id}")
        return {'success': True, 'action': 'rollback', 'message': 'Changes discarded'}
    else:
        return {'success': False, 'error': 'Rollback verification failed'}


def run_phase2_accept(transaction_id):
    """
    Phase 2b: Accept changes (no rollback needed).
    
    This corresponds to API endpoint for "Confirm/Commit" button.
    
    Args:
        transaction_id: from Phase 1 response
        
    Returns:
        dict with success status and message
    """
    if transaction_id not in PENDING_SAVEPOINTS:
        return {'success': False, 'error': f'Transaction {transaction_id} not found'}
    
    pending = PENDING_SAVEPOINTS[transaction_id]
    dump_file = pending['dump_file']
    
    # Just cleanup - don't restore
    if os.path.exists(dump_file):
        os.remove(dump_file)
    del PENDING_SAVEPOINTS[transaction_id]
    
    print(f"Accept complete: {transaction_id}")
    return {'success': True, 'action': 'accept', 'message': 'Changes committed'}


def get_pending_transaction(proposal_id):
    """Get pending transaction for a proposal (if any)"""
    for tid, data in PENDING_SAVEPOINTS.items():
        if data['proposal_id'] == proposal_id:
            return {'transaction_id': tid, **data}
    return None


def clear_pending_transaction(transaction_id):
    """Clear a pending transaction without rollback (emergency cleanup)"""
    if transaction_id in PENDING_SAVEPOINTS:
        pending = PENDING_SAVEPOINTS[transaction_id]
        dump_file = pending['dump_file']
        if os.path.exists(dump_file):
            os.remove(dump_file)
        del PENDING_SAVEPOINTS[transaction_id]
        return {'success': True}
    return {'success': False, 'error': 'Transaction not found'}


def get_table_counts():
    """Query table row counts for verification"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name, record_count FROM (
                SELECT 'polygon' AS table_name, COUNT(*) AS record_count FROM polygon
                UNION ALL
                SELECT 'cohort', COUNT(*) FROM cohort
                UNION ALL
                SELECT 'assign_cht_to_ply', COUNT(*) FROM assign_cht_to_ply
                UNION ALL
                SELECT 'treatment', COUNT(*) FROM treatment
                UNION ALL
                SELECT 'treatment_xtra', COUNT(*) FROM treatment_xtra
                UNION ALL
                SELECT 'proposal', COUNT(*) FROM proposal
            ) AS counts ORDER BY table_name
        """)
        return cursor.fetchall()


def get_table_counts_dict():
    """Query table row counts as a dictionary"""
    counts = get_table_counts()
    return {table_name: count for table_name, count in counts}


def print_table_counts(label):
    print(f"\n=== {label} ===")
    counts = get_table_counts()
    for table_name, count in counts:
        print(f"{table_name:20} | {count}")
    return counts


def get_affected_tables(baseline_counts, after_counts):
    """
    Compare baseline and after counts to determine which tables changed.

    Args:
        baseline_counts: dict of table_name -> count (before processing)
        after_counts: dict of table_name -> count (after processing)

    Returns:
        list of table names that have changed
    """
    affected = []
    baseline_dict = dict(baseline_counts)
    after_dict = dict(after_counts)

    for table in AFFECTED_TABLES:
        baseline_count = baseline_dict.get(table, 0)
        after_count = after_dict.get(table, 0)
        if baseline_count != after_count:
            diff = after_count - baseline_count
            affected.append({
                'table': table,
                'baseline': baseline_count,
                'after': after_count,
                'diff': diff,
            })

    return affected


def dump_affected_tables(affected_tables, dump_file, schema='silrec'):
    """
    Dump specific tables to a file using pg_dump in custom format.
    
    Args:
        affected_tables: list of table names (strings) OR list of dicts with 'table' key
        dump_file: output file path
        schema: PostgreSQL schema name (default: 'silrec')
    """
    # Handle both string and dict inputs
    if affected_tables and isinstance(affected_tables[0], dict):
        affected_names = [t['table'] for t in affected_tables]
    else:
        affected_names = affected_tables
    
    # Build command with multiple -t flags, use -Fc for custom format
    cmd = [
        'pg_dump', '-h', 'localhost', '-p', '5432', '-U', 'dev',
        '-d', 'silrec_test3',
        '-Fc',  # custom format (required for pg_restore)
        '-f', dump_file,
    ]
    # Add -t for each table with schema prefix
    for t in affected_names:
        cmd.extend(['-t', f'{schema}.{t}'])
    
    print(f"Dumping affected tables: {affected_names}")
    subprocess.run(cmd, env={'PGPASSWORD': 'dev123'}, check=True)
    print(f"Dumped to: {dump_file}")


def restore_affected_tables(affected_tables, dump_file, schema='silrec'):
    """
    Restore specific tables from a dump file using pg_restore.
    
    Args:
        affected_tables: list of table names (strings) OR list of dicts with 'table' key
        dump_file: input file path
        schema: PostgreSQL schema name (default: 'silrec')
    """
    # Handle both string and dict inputs
    if affected_tables and isinstance(affected_tables[0], dict):
        affected_names = [t['table'] for t in affected_tables]
    else:
        affected_names = affected_tables
    
    # Restore dependent tables first (FK order matters)
    # order: polygon -> cohort -> assign_cht_to_ply
    table_order = ['polygon', 'cohort', 'assign_cht_to_ply']
    
    for table_name in table_order:
        if table_name not in affected_names:
            continue
            
        cmd = [
            'pg_restore', '-h', 'localhost', '-p', '5432', '-U', 'dev',
            '-d', 'silrec_test3',
            '-c',  # clean (drop)
            '--if-exists',  # don't error if doesn't exist
            '-1',  # single transaction
            '--disable-triggers',  # disable triggers during restore
            dump_file,
            '-t', f'{schema}.{table_name}',
        ]
        
        print(f"Restoring table: {table_name}")
        result = subprocess.run(cmd, env={'PGPASSWORD': 'dev123'}, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            raise CalledProcessError(result.returncode, cmd)
    
    print(f"Restored from: {dump_file}")


def reset_database():
    """Reset database to baseline state"""
    drop_prod_tables_django()
    import subprocess
    subprocess.run([
        'pg_restore', '-h', 'localhost', '-p', '5432', '-U', 'dev',
        '-d', 'silrec_test3', 'silrec_3tables_14Mar2026.dump'
    ], env={'PGPASSWORD': 'dev123'}, check=True)


def rollback_to_savepoint_django(savepoint_id):
    """Rollback to a Django savepoint"""
    transaction.savepoint_rollback(savepoint_id)


def commit_savepoint(savepoint_id):
    """Commit a Django savepoint"""
    transaction.savepoint_commit(savepoint_id)


def create_sql_savepoint(name):
    """Create a PostgreSQL savepoint using raw SQL - MUST be inside atomic block"""
    with connection.cursor() as cursor:
        cursor.execute(f"SAVEPOINT {name}")


def rollback_to_sql_savepoint(name):
    """Rollback to a PostgreSQL savepoint using raw SQL - MUST be inside atomic block"""
    with connection.cursor() as cursor:
        cursor.execute(f"ROLLBACK TO SAVEPOINT {name}")


def release_sql_savepoint(name):
    """Release a PostgreSQL savepoint (make changes permanent from that point) - MUST be inside atomic block"""
    with connection.cursor() as cursor:
        cursor.execute(f"RELEASE SAVEPOINT {name}")


def run_with_rollback_test(do_rollback=True):
    """
    Test rollback strategy using Django savepoints.

    Strategy: All operations inside one atomic block with savepoints.
    At the end, decide whether to rollback or commit.

    Args:
        do_rollback: If True, rollback to savepoint. If False, commit changes.
    """
    print("=" * 60)
    print("TEST: Rollback Strategy with Django Savepoints")
    print("=" * 60)

    # Reset to baseline
    print("\n--- Resetting Database ---")
    reset_database()
    baseline_counts = print_table_counts("BASELINE (after pg_restore)")

    # Process with savepoints inside atomic block
    print("\n--- Running Processing with Savepoints ---")

    with transaction.atomic():
        # Create savepoint AFTER reset (baseline state)
        sid_after_reset = transaction.savepoint()
        print(f"Created savepoint: sid_after_reset = {sid_after_reset}")

        # Run the processing
        ssm = ShapefileSliversMerger(proposal_id=1, threshold=5, user_id=1)
        list_state = ssm.create_gdf()

        after_processing_counts = print_table_counts("AFTER PROCESSING (before decision)")

        # === ROLLBACK DECISION POINT ===

        if do_rollback:
            # Rollback to baseline (discard all changes)
            print("\n--- Rolling back to baseline ---")
            transaction.savepoint_rollback(sid_after_reset)
            transaction.savepoint_commit(sid_after_reset)  # Release savepoint
        else:
            # Commit changes
            print("\n--- Committing changes ---")
            transaction.savepoint_commit(sid_after_reset)

    # After atomic block exits, transaction is committed
    final_counts = print_table_counts("FINAL")

    # Verify we returned to baseline
    print("\n--- Verification ---")
    if do_rollback:
        if final_counts == baseline_counts:
            print("SUCCESS: Rollback worked! Table counts match baseline.")
        else:
            print("FAILED: Table counts do not match baseline.")
            print("Difference:")
            for i, (tbl, baseline_count) in enumerate(baseline_counts):
                final_count = final_counts[i][1]
                diff = final_count - baseline_count
                print(f"  {tbl}: {baseline_count} -> {final_count} ({diff:+d})")
    else:
        print("Changes committed (do_rollback=False)")

    return list_state


def run_with_sql_savepoint_test(do_rollback=True):
    """
    Alternative: Test rollback strategy using PostgreSQL SAVEPOINTs.

    This uses raw SQL savepoints which can be rolled back even after
    Django's atomic block exits (within the same session).

    Args:
        do_rollback: If True, rollback to savepoint. If False, release savepoint (keep changes).
    """
    print("=" * 60)
    print("TEST: Rollback Strategy with SQL Savepoints")
    print("=" * 60)

    # Reset to baseline
    print("\n--- Resetting Database ---")
    reset_database()
    baseline_counts = print_table_counts("BASELINE (after pg_restore)")

    # ALL savepoint operations must be inside an atomic block
    with transaction.atomic():
        # Create PostgreSQL savepoint BEFORE processing
        print("\n--- Creating SQL Savepoint ---")
        create_sql_savepoint("baseline_sp")

        # Run the processing (no Django atomic inside now)
        ssm = ShapefileSliversMerger(proposal_id=1, threshold=5, user_id=1)
        list_state = ssm.create_gdf()

        after_processing_counts = print_table_counts("AFTER PROCESSING (inside atomic)")

        # Decision: rollback or commit
        if do_rollback:
            print("\n--- Rolling back to SQL savepoint ---")
            rollback_to_sql_savepoint("baseline_sp")
        else:
            print("\n--- Releasing SQL savepoint (keeping changes) ---")
            release_sql_savepoint("baseline_sp")

    final_counts = print_table_counts("FINAL")

    # Verify
    print("\n--- Verification ---")
    if do_rollback:
        if final_counts == baseline_counts:
            print("SUCCESS: SQL Savepoint rollback worked!")
        else:
            print("FAILED: Table counts do not match baseline.")
    else:
        print(f"Changes kept (do_rollback=False)")

    return list_state


def run_full_rollback_test():
    """
    Full rollback test - reset database after processing to verify baseline.
    This is the most reliable method.
    """
    print("=" * 60)
    print("TEST: Full Reset After Processing")
    print("=" * 60)

    # Reset to baseline
    print("\n--- Resetting Database ---")
    reset_database()
    baseline_counts = print_table_counts("BASELINE (after pg_restore)")

    # Run processing WITHOUT any transaction management
    print("\n--- Running Processing ---")
    ssm = ShapefileSliversMerger(proposal_id=1, threshold=5, user_id=1)
    list_state = ssm.create_gdf()

    after_processing_counts = print_table_counts("AFTER PROCESSING")

    # Rollback by restoring from dump again
    print("\n--- Rolling back (resetting database again) ---")
    reset_database()
    final_counts = print_table_counts("FINAL (after reset)")

    # Verify
    print("\n--- Verification ---")
    if final_counts == baseline_counts:
        print("SUCCESS: Full reset rollback worked!")
    else:
        print("FAILED: Table counts do not match baseline.")

    return list_state


def run_phase1_create_gdf(proposal_id, user_id):
    """
    Phase 1: Run create_gdf with savepoint, store savepoint name.
    This would be an API endpoint called from web page.

    Returns:
        dict with list_state results and a transaction_id to reference later
    """
    import uuid

    # Generate unique transaction ID
    transaction_id = f"sp_{proposal_id}_{uuid.uuid4().hex[:8]}"

    with transaction.atomic():
        # Create PostgreSQL savepoint
        create_sql_savepoint(transaction_id)

        # Run processing
        ssm = ShapefileSliversMerger(proposal_id=proposal_id, threshold=5, user_id=user_id)
        list_state = ssm.create_gdf()

        # Store savepoint name for later use (in production, save to Proposal model)
        PENDING_SAVEPOINTS[transaction_id] = {
            'savepoint_name': transaction_id,
            'proposal_id': proposal_id,
        }

        print(f"Phase 1 complete. Transaction ID: {transaction_id}")
        print(f"Savepoint '{transaction_id}' saved. Call phase2_rollback() or phase2_commit() with this ID.")

    return {
        'transaction_id': transaction_id,
        'list_state': list_state,
    }


def run_phase2_rollback(transaction_id):
    """
    Phase 2a: Rollback to the savepoint created in phase 1.
    This would be an API endpoint for "Reject/Discard" button on web page.
    """
    if transaction_id not in PENDING_SAVEPOINTS:
        print(f"ERROR: No pending savepoint found for {transaction_id}")
        return {'success': False, 'error': 'Transaction not found'}

    with transaction.atomic():
        print(f"Rolling back to savepoint: {transaction_id}")
        rollback_to_sql_savepoint(transaction_id)

    del PENDING_SAVEPOINTS[transaction_id]
    print(f"Rollback complete. Transaction {transaction_id} removed.")
    return {'success': True, 'action': 'rollback'}


def run_phase2_commit(transaction_id):
    """
    Phase 2b: Release savepoint (keep changes).
    This would be an API endpoint for "Confirm/Commit" button on web page.
    """
    if transaction_id not in PENDING_SAVEPOINTS:
        print(f"ERROR: No pending savepoint found for {transaction_id}")
        return {'success': False, 'error': 'Transaction not found'}

    with transaction.atomic():
        print(f"Releasing savepoint (keeping changes): {transaction_id}")
        release_sql_savepoint(transaction_id)

    del PENDING_SAVEPOINTS[transaction_id]
    print(f"Commit complete. Transaction {transaction_id} removed.")
    return {'success': True, 'action': 'commit'}


def list_pending_savepoints():
    """List all pending transactions"""
    return PENDING_SAVEPOINTS.copy()


def run_with_dump_restore_test():
    """
    Test rollback strategy using pg_dump/pg_restore for affected tables.
    
    Phase 1: Reset DB and dump baseline BEFORE processing
    Phase 2: Run processing
    Phase 3: Restore affected tables on rollback
    """
    print("=" * 60)
    print("TEST: Rollback Strategy with pg_dump/pg_restore")
    print("=" * 60)

    import os

    # Reset to baseline
    print("\n--- Resetting Database ---")
    reset_database()
    baseline_counts = print_table_counts("BASELINE (after pg_restore)")
    baseline_dict = dict(baseline_counts)

    # Phase 1: Dump affected tables BEFORE processing (this creates the baseline backup)
    dump_file = '/tmp/affected_tables.dump'
    affected_for_dump = [{'table': t} for t in AFFECTED_TABLES]
    print(f"\n--- Dumping affected tables to {dump_file} (baseline) ---")
    dump_affected_tables(affected_for_dump, dump_file)

    # Phase 2: Run processing
    print("\n--- Running Processing ---")
    ssm = ShapefileSliversMerger(proposal_id=1, threshold=5, user_id=1)
    list_state = ssm.create_gdf()

    after_processing_counts = print_table_counts("AFTER PROCESSING")
    after_dict = dict(after_processing_counts)

    # Determine which tables changed (for reporting)
    before_counts = get_table_counts_dict()
    affected = get_affected_tables(before_counts, after_dict)
    print("Tables with changes:")
    for t in affected:
        print(f"  {t['table']}: {t['baseline']} -> {t['after']} ({t['diff']:+d})")

    # Phase 3: Restore from baseline dump (rollback)
    print("\n--- Rolling back (restoring affected tables from baseline) ---")
    restore_affected_tables(AFFECTED_TABLES, dump_file)

    final_counts = print_table_counts("FINAL (after restore)")
    final_dict = dict(final_counts)

    # Verify
    print("\n--- Verification ---")
    success = True
    for t in affected:
        baseline_count = baseline_dict.get(t['table'])
        final_count = final_dict.get(t['table'])
        if final_count != baseline_count:
            print(f"FAILED: {t['table']} baseline={baseline_count}, final={final_count}")
            success = False
        else:
            print(f"OK: {t['table']} = {final_count}")

    if success:
        print("SUCCESS: Affected tables restored to baseline!")
    else:
        print("FAILED: Table counts do not match baseline.")

    # Cleanup
    if os.path.exists(dump_file):
        os.remove(dump_file)

    return list_state


if __name__ == "__main__":
    # Choose which test to run:

    # Test 1: Django savepoint rollback (recommended)
    # list_state = run_with_rollback_test()

    # Test 2: SQL savepoint rollback (alternative)
    # list_state = run_with_sql_savepoint_test()

    # Test 3: Full reset (most reliable but slowest)
    # list_state = run_full_rollback_test()

    # Test 4: pg_dump/pg_restore for affected tables
    list_state = run_with_dump_restore_test()

    print(len(list_state[0]['GDF_RESULT_COMBINED']))
