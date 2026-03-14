import json
import os
import datetime
import hashlib
from django.core.serializers import serialize
from django.db import connection
from django.conf import settings
import difflib
import pandas as pd

# Make tabulate optional - if not available, we'll use a simple fallback
try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    # Simple fallback for tabulate
    def tabulate(data, headers='keys', tablefmt='simple', showindex=False):
        if not data:
            return "No data"
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # Simple formatting for list of dicts
            result = []
            headers_list = list(data[0].keys())
            result.append(" | ".join(headers_list))
            result.append("-" * 50)
            for row in data:
                result.append(" | ".join(str(row.get(h, '')) for h in headers_list))
            return "\n".join(result)
        return str(data)

class SnapshotManager:
    """
    Utility class to create and compare snapshots of database tables
    for testing and verification purposes.
    """

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.snapshot_dir = os.path.join(settings.BASE_DIR, 'snapshots')
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)

    def get_affected_tables(self):
        """
        Return list of tables that are typically modified during shapefile processing
        """
        return [
            'polygon',
            'cohort',
            'assign_cht_to_ply',
            'treatment',
            'treatment_xtra',
            'proposal',
        ]

    def get_table_schema(self, table_name):
        """
        Get schema information for a table
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, [table_name])

            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3]
                })
            return columns

    def create_snapshot(self, proposal_id, user_id, tag=None):
        """
        Create a snapshot of all affected tables for a given proposal

        Args:
            proposal_id: The proposal ID
            user_id: User ID creating the snapshot
            tag: Optional tag to identify the snapshot (e.g., 'before_process', 'after_revert')

        Returns:
            dict: Snapshot metadata and data
        """
        timestamp = datetime.datetime.now().isoformat()
        snapshot_id = hashlib.md5(f"{proposal_id}_{timestamp}".encode()).hexdigest()[:8]

        if not tag:
            tag = f"snapshot_{timestamp}"

        snapshot = {
            'id': snapshot_id,
            'proposal_id': proposal_id,
            'user_id': user_id,
            'timestamp': timestamp,
            'tag': tag,
            'tables': {},
            'metadata': {
                'proposal_state': self._get_proposal_state(proposal_id),
                'record_counts': {}
            }
        }

        affected_tables = self.get_affected_tables()

        for table_name in affected_tables:
            table_data = self._snapshot_table(table_name, proposal_id)
            snapshot['tables'][table_name] = table_data
            snapshot['metadata']['record_counts'][table_name] = len(table_data['records'])

        # Save snapshot to file
        filename = f"snapshot_{proposal_id}_{snapshot_id}_{tag}.json"
        filepath = os.path.join(self.snapshot_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)

        # Also save a summary
        self._save_summary(snapshot, filepath.replace('.json', '_summary.txt'))

        return snapshot

    def _get_proposal_state(self, proposal_id):
        """
        Get key fields from proposal to track its state
        """
        from silrec.components.proposals.models import Proposal

        try:
            proposal = Proposal.objects.get(id=proposal_id)
            return {
                'id': proposal.id,
                'processing_status': proposal.processing_status,
                'lodgement_number': proposal.lodgement_number,
                'has_shapefile': bool(proposal.shapefile_json),
                'has_processed': bool(proposal.geojson_data_processed),
                'has_processed_iters': bool(proposal.geojson_data_processed_iters),
                'shapefile_name': getattr(proposal, 'shapefile_name', None),
            }
        except Proposal.DoesNotExist:
            return None

    def _snapshot_table(self, table_name, proposal_id):
        """
        Create a snapshot of a specific table, filtered by proposal if possible
        """
        records = []

        with connection.cursor() as cursor:
            # First, try to find if table has proposal relationship
            proposal_relations = {
                'polygon': 'proposal_id',
                'cohort': None,  # Need to go through assign_cht_to_ply
                'assign_cht_to_ply': None,  # Need to go through polygon
                'treatment': None,  # Need to go through cohort
                'treatment_xtra': None,  # Need to go through treatment
                'proposal': 'id',
            }

            if table_name == 'polygon' and proposal_relations.get(table_name) == 'proposal_id':
                # Direct relationship
                cursor.execute(f"SELECT * FROM {table_name} WHERE proposal_id = %s", [proposal_id])
            elif table_name == 'proposal':
                cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", [proposal_id])
            elif table_name in ['cohort', 'treatment', 'treatment_xtra', 'assign_cht_to_ply']:
                # Need to get related records through joins
                self._get_related_records(cursor, table_name, proposal_id)
            else:
                # No filtering, but limit to 1000 for safety
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")

            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            for row in rows:
                record = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert to JSON-serializable format
                    if hasattr(value, 'isoformat'):  # datetime/date
                        value = value.isoformat()
                    elif hasattr(value, 'wkb'):  # geometry
                        value = str(value)
                    elif hasattr(value, 'wkt'):  # geometry
                        value = str(value)
                    record[col] = value
                records.append(record)

        # Get schema
        schema = self.get_table_schema(table_name)

        return {
            'records': records,
            'count': len(records),
            'schema': schema
        }

    def _get_related_records(self, cursor, table_name, proposal_id):
        """
        Get records from related tables through joins
        """
        if table_name == 'cohort':
            cursor.execute("""
                SELECT DISTINCT c.*
                FROM cohort c
                INNER JOIN assign_cht_to_ply acp ON acp.cohort_id = c.cohort_id
                INNER JOIN polygon p ON p.polygon_id = acp.polygon_id
                WHERE p.proposal_id = %s
            """, [proposal_id])
        elif table_name == 'assign_cht_to_ply':
            cursor.execute("""
                SELECT acp.*
                FROM assign_cht_to_ply acp
                INNER JOIN polygon p ON p.polygon_id = acp.polygon_id
                WHERE p.proposal_id = %s
            """, [proposal_id])
        elif table_name == 'treatment':
            cursor.execute("""
                SELECT DISTINCT t.*
                FROM treatment t
                INNER JOIN cohort c ON c.cohort_id = t.cohort_id
                INNER JOIN assign_cht_to_ply acp ON acp.cohort_id = c.cohort_id
                INNER JOIN polygon p ON p.polygon_id = acp.polygon_id
                WHERE p.proposal_id = %s
            """, [proposal_id])
        elif table_name == 'treatment_xtra':
            cursor.execute("""
                SELECT DISTINCT tx.*
                FROM treatment_xtra tx
                INNER JOIN treatment t ON t.treatment_id = tx.treatment_id
                INNER JOIN cohort c ON c.cohort_id = t.cohort_id
                INNER JOIN assign_cht_to_ply acp ON acp.cohort_id = c.cohort_id
                INNER JOIN polygon p ON p.polygon_id = acp.polygon_id
                WHERE p.proposal_id = %s
            """, [proposal_id])

    def _save_summary(self, snapshot, filepath):
        """
        Save a human-readable summary of the snapshot
        """
        with open(filepath, 'w') as f:
            f.write(f"SNAPSHOT SUMMARY\n")
            f.write(f"===============\n\n")
            f.write(f"ID: {snapshot['id']}\n")
            f.write(f"Proposal: {snapshot['proposal_id']}\n")
            f.write(f"User: {snapshot['user_id']}\n")
            f.write(f"Timestamp: {snapshot['timestamp']}\n")
            f.write(f"Tag: {snapshot['tag']}\n\n")

            f.write("Proposal State:\n")
            f.write("-" * 20 + "\n")
            for key, value in snapshot['metadata']['proposal_state'].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")

            f.write("Record Counts:\n")
            f.write("-" * 20 + "\n")
            for table, count in snapshot['metadata']['record_counts'].items():
                f.write(f"  {table}: {count}\n")
            f.write("\n")

            f.write("Table Details:\n")
            f.write("-" * 20 + "\n")
            for table_name, table_data in snapshot['tables'].items():
                f.write(f"\n{table_name}:\n")
                if table_data['records']:
                    # Show first few records as sample
                    sample = table_data['records'][:3]
                    df = pd.DataFrame(sample)
                    f.write(tabulate(df, headers='keys', tablefmt='simple', showindex=False))
                    if len(table_data['records']) > 3:
                        f.write(f"\n  ... and {len(table_data['records']) - 3} more records\n")
                else:
                    f.write("  No records\n")

    def compare_snapshots(self, snapshot1_id, snapshot2_id):
        """
        Compare two snapshots and return differences
        """
        # Load snapshots
        snapshots = self._load_snapshots()
        snapshot1 = snapshots.get(snapshot1_id)
        snapshot2 = snapshots.get(snapshot2_id)

        if not snapshot1 or not snapshot2:
            return {'error': 'One or both snapshots not found'}

        comparison = {
            'snapshot1': {
                'id': snapshot1['id'],
                'tag': snapshot1['tag'],
                'timestamp': snapshot1['timestamp']
            },
            'snapshot2': {
                'id': snapshot2['id'],
                'tag': snapshot2['tag'],
                'timestamp': snapshot2['timestamp']
            },
            'proposal_changes': self._compare_proposal_states(
                snapshot1['metadata']['proposal_state'],
                snapshot2['metadata']['proposal_state']
            ),
            'tables': {},
            'summary': {
                'tables_with_changes': [],
                'total_changes': 0,
                'tables_unchanged': []
            }
        }

        all_tables = set(snapshot1['tables'].keys()) | set(snapshot2['tables'].keys())

        for table_name in all_tables:
            table1 = snapshot1['tables'].get(table_name, {'records': [], 'count': 0})
            table2 = snapshot2['tables'].get(table_name, {'records': [], 'count': 0})

            table_comparison = self._compare_tables(table_name, table1, table2)
            comparison['tables'][table_name] = table_comparison

            if table_comparison['has_changes']:
                comparison['summary']['tables_with_changes'].append(table_name)
                comparison['summary']['total_changes'] += table_comparison['total_differences']
            else:
                comparison['summary']['tables_unchanged'].append(table_name)

        # Save comparison to file
        self._save_comparison(comparison)

        return comparison

    def _load_snapshots(self):
        """
        Load all snapshots from the snapshot directory
        """
        snapshots = {}
        if not os.path.exists(self.snapshot_dir):
            return snapshots

        for filename in os.listdir(self.snapshot_dir):
            if filename.endswith('.json') and not filename.endswith('_summary.txt'):
                filepath = os.path.join(self.snapshot_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        snapshot = json.load(f)
                        snapshots[snapshot['id']] = snapshot
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error loading snapshot {filename}: {e}")
        return snapshots

    def _compare_proposal_states(self, state1, state2):
        """
        Compare two proposal states
        """
        if not state1 or not state2:
            return {'has_changes': True, 'changes': {'state': 'One or both states missing'}}

        changes = {}
        all_keys = set(state1.keys()) | set(state2.keys())

        for key in all_keys:
            val1 = state1.get(key)
            val2 = state2.get(key)
            if val1 != val2:
                changes[key] = {
                    'before': val1,
                    'after': val2
                }

        return {
            'has_changes': len(changes) > 0,
            'changes': changes
        }

    def _compare_tables(self, table_name, table1, table2):
        """
        Compare two table snapshots
        """
        records1 = {self._get_record_id(rec): rec for rec in table1['records']}
        records2 = {self._get_record_id(rec): rec for rec in table2['records']}

        ids1 = set(records1.keys())
        ids2 = set(records2.keys())

        added = ids2 - ids1
        removed = ids1 - ids2
        common = ids1 & ids2

        modified = []
        for record_id in common:
            if records1[record_id] != records2[record_id]:
                modified.append({
                    'id': record_id,
                    'before': records1[record_id],
                    'after': records2[record_id],
                    'differences': self._get_record_differences(
                        records1[record_id], records2[record_id]
                    )
                })

        return {
            'has_changes': bool(added or removed or modified),
            'count_before': table1['count'],
            'count_after': table2['count'],
            'added': list(added),
            'removed': list(removed),
            'modified': modified,
            'added_count': len(added),
            'removed_count': len(removed),
            'modified_count': len(modified),
            'total_differences': len(added) + len(removed) + len(modified)
        }

    def _get_record_id(self, record):
        """
        Extract record ID from a record dictionary
        """
        id_fields = ['polygon_id', 'cohort_id', 'cht2ply_id', 'treatment_id',
                    'treatment_xtra_id', 'id', 'record_id']

        for field in id_fields:
            if field in record and record[field] is not None:
                return f"{field}:{record[field]}"

        # If no ID field found, use first field as fallback
        if record:
            first_key = list(record.keys())[0]
            return f"{first_key}:{record[first_key]}"

        return None

    def _get_record_differences(self, rec1, rec2):
        """
        Get detailed differences between two records
        """
        differences = []
        all_keys = set(rec1.keys()) | set(rec2.keys())

        for key in all_keys:
            val1 = rec1.get(key)
            val2 = rec2.get(key)
            if val1 != val2:
                differences.append({
                    'field': key,
                    'before': val1,
                    'after': val2
                })

        return differences

    def _save_comparison(self, comparison):
        """
        Save comparison results to a file
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comparison_{comparison['snapshot1']['id']}_vs_{comparison['snapshot2']['id']}_{timestamp}.json"
        filepath = os.path.join(self.snapshot_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)

        # Also save a human-readable summary
        self._save_comparison_summary(comparison, filepath.replace('.json', '_summary.txt'))

    def _save_comparison_summary(self, comparison, filepath):
        """
        Save a human-readable comparison summary
        """
        with open(filepath, 'w') as f:
            f.write("SNAPSHOT COMPARISON SUMMARY\n")
            f.write("===========================\n\n")

            f.write(f"Snapshot 1: {comparison['snapshot1']['tag']} ({comparison['snapshot1']['timestamp']})\n")
            f.write(f"Snapshot 2: {comparison['snapshot2']['tag']} ({comparison['snapshot2']['timestamp']})\n\n")

            f.write("Proposal Changes:\n")
            f.write("-" * 20 + "\n")
            if comparison['proposal_changes']['has_changes']:
                for key, change in comparison['proposal_changes']['changes'].items():
                    f.write(f"  {key}: {change['before']} -> {change['after']}\n")
            else:
                f.write("  No changes\n")
            f.write("\n")

            f.write("Summary:\n")
            f.write("-" * 20 + "\n")
            f.write(f"  Tables with changes: {len(comparison['summary']['tables_with_changes'])}\n")
            f.write(f"  Total changes: {comparison['summary']['total_changes']}\n")
            f.write(f"  Tables unchanged: {len(comparison['summary']['tables_unchanged'])}\n\n")

            for table_name, table_comp in comparison['tables'].items():
                f.write(f"\n{table_name}:\n")
                f.write(f"  Count: {table_comp['count_before']} -> {table_comp['count_after']}\n")
                if table_comp['has_changes']:
                    f.write(f"  Added: {table_comp['added_count']}\n")
                    f.write(f"  Removed: {table_comp['removed_count']}\n")
                    f.write(f"  Modified: {table_comp['modified_count']}\n")

                    if table_comp['modified']:
                        f.write("\n  Modified Records:\n")
                        for mod in table_comp['modified'][:5]:  # Limit to 5 examples
                            f.write(f"    ID: {mod['id']}\n")
                            for diff in mod['differences'][:3]:  # Limit to 3 field changes
                                f.write(f"      {diff['field']}: {diff['before']} -> {diff['after']}\n")
                            if len(mod['differences']) > 3:
                                f.write(f"      ... and {len(mod['differences']) - 3} more fields\n")
                            f.write("\n")
                else:
                    f.write("  No changes\n")

    def list_snapshots(self, proposal_id=None):
        """
        List all available snapshots, optionally filtered by proposal
        """
        snapshots = self._load_snapshots()

        if proposal_id:
            snapshots = {k: v for k, v in snapshots.items()
                        if v.get('proposal_id') == proposal_id}

        # Sort by timestamp (newest first)
        sorted_snapshots = sorted(
            snapshots.values(),
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )

        return sorted_snapshots

    def get_snapshot(self, snapshot_id):
        """
        Get a specific snapshot by ID
        """
        snapshots = self._load_snapshots()
        return snapshots.get(snapshot_id)


class SnapshotTestMixin:
    """
    Mixin for test classes to easily use snapshots
    """

    def setUp(self):
        super().setUp()
        self.snapshot_manager = SnapshotManager(test_mode=True)
        self.snapshot_ids = []

    def create_before_snapshot(self, proposal_id, user_id):
        """Create a 'before' snapshot"""
        snapshot = self.snapshot_manager.create_snapshot(
            proposal_id, user_id, tag='test_before'
        )
        self.snapshot_ids.append(snapshot['id'])
        return snapshot

    def create_after_snapshot(self, proposal_id, user_id, tag='test_after'):
        """Create an 'after' snapshot"""
        snapshot = self.snapshot_manager.create_snapshot(
            proposal_id, user_id, tag=tag
        )
        self.snapshot_ids.append(snapshot['id'])
        return snapshot

    def compare_last_two_snapshots(self):
        """Compare the last two snapshots created"""
        if len(self.snapshot_ids) >= 2:
            return self.snapshot_manager.compare_snapshots(
                self.snapshot_ids[-2], self.snapshot_ids[-1]
            )
        return None

    def assertSnapshotEqual(self, snapshot1_id, snapshot2_id, tables=None):
        """
        Assert that two snapshots are equal (no changes)
        """
        comparison = self.snapshot_manager.compare_snapshots(
            snapshot1_id, snapshot2_id
        )

        if 'error' in comparison:
            self.fail(comparison['error'])

        if tables:
            # Check only specified tables
            for table in tables:
                self.assertFalse(
                    comparison['tables'][table]['has_changes'],
                    f"Table {table} has unexpected changes"
                )
        else:
            # Check all tables
            self.assertEqual(
                comparison['summary']['total_changes'], 0,
                f"Expected no changes but found {comparison['summary']['total_changes']}"
            )

