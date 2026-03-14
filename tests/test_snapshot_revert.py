# silrec/tests/test_snapshot_revert.py

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from silrec.components.proposals.models import Proposal
from silrec.utils.snapshot_utils import SnapshotManager, SnapshotTestMixin
import json

class SnapshotRevertTest(TransactionTestCase, SnapshotTestMixin):
    """Test class to verify snapshot and revert functionality"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.proposal = Proposal.objects.create(
            title='Test Proposal',
            submitter=self.user.id,
            # Add other required fields
        )

    def test_snapshot_creation(self):
        """Test that snapshots are created correctly"""
        # Create before snapshot
        before = self.create_before_snapshot(self.proposal.id, self.user.id)

        # Perform some operation (simulate shapefile processing)
        self.simulate_shapefile_processing()

        # Create after snapshot
        after = self.create_after_snapshot(self.proposal.id, self.user.id, 'after_process')

        # Compare snapshots
        comparison = self.compare_last_two_snapshots()

        # Verify changes are detected
        self.assertIsNotNone(comparison)
        self.assertGreater(comparison['summary']['total_changes'], 0)

        # Verify specific tables have changes
        self.assertTrue(comparison['tables']['polygon']['has_changes'])

        # Save test results
        self.save_test_results(comparison)

    def test_revert_verification(self):
        """Test that revert correctly restores state"""
        # Create before snapshot
        before = self.create_before_snapshot(self.proposal.id, self.user.id)

        # Simulate shapefile processing
        self.simulate_shapefile_processing()

        # Perform revert operation
        self.simulate_revert()

        # Create after revert snapshot
        after_revert = self.create_after_snapshot(
            self.proposal.id, self.user.id, 'after_revert'
        )

        # Compare before and after revert
        comparison = self.snapshot_manager.compare_snapshots(
            before['id'], after_revert['id']
        )

        # Verify no differences (revert was successful)
        self.assertEqual(
            comparison['summary']['total_changes'], 0,
            "Revert did not restore original state"
        )

        # Save test results
        self.save_test_results(comparison, 'revert_test')

    def simulate_shapefile_processing(self):
        """Simulate shapefile processing - to be implemented"""
        # This would call your actual ProcessShapefileView
        pass

    def simulate_revert(self):
        """Simulate revert - to be implemented"""
        # This would call your actual RevertShapefileProcessingView
        pass

    def save_test_results(self, comparison, test_name='snapshot_test'):
        """Save test results to file for review"""
        import os
        from django.conf import settings

        results_dir = os.path.join(settings.BASE_DIR, 'test_results')
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        filename = f"{test_name}_{comparison['snapshot1']['id']}_vs_{comparison['snapshot2']['id']}.json"
        filepath = os.path.join(results_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)

        print(f"\nTest results saved to: {filepath}")


class ManualSnapshotVerification:
    """
    Helper class for manual verification during development
    """

    def __init__(self, proposal_id, user_id):
        self.proposal_id = proposal_id
        self.user_id = user_id
        self.sm = SnapshotManager()
        self.snapshots = []

    def take_snapshot(self, tag):
        """Take a manual snapshot"""
        snapshot = self.sm.create_snapshot(
            self.proposal_id, self.user_id, tag
        )
        self.snapshots.append(snapshot)
        print(f"Snapshot created: {snapshot['id']} - {tag}")
        return snapshot

    def verify_operation(self, before_tag, after_tag):
        """Verify an operation by comparing before/after snapshots"""
        # Find snapshots by tag
        snapshots = self.sm.list_snapshots(self.proposal_id)
        before = next((s for s in snapshots if s['tag'] == before_tag), None)
        after = next((s for s in snapshots if s['tag'] == after_tag), None)

        if not before or not after:
            print(f"Could not find snapshots with tags: {before_tag}, {after_tag}")
            return None

        comparison = self.sm.compare_snapshots(before['id'], after['id'])

        # Print summary
        print("\n" + "="*50)
        print("VERIFICATION RESULTS")
        print("="*50)
        print(f"Before: {before['tag']} ({before['timestamp']})")
        print(f"After: {after['tag']} ({after['timestamp']})")
        print(f"\nTotal Changes: {comparison['summary']['total_changes']}")
        print(f"Tables with changes: {comparison['summary']['tables_with_changes']}")
        print(f"Tables unchanged: {comparison['summary']['tables_unchanged']}")

        # Print detailed changes
        for table_name, table_comp in comparison['tables'].items():
            if table_comp['has_changes']:
                print(f"\n{table_name}:")
                print(f"  Count: {table_comp['count_before']} → {table_comp['count_after']}")
                print(f"  Added: {table_comp['added_count']}")
                print(f"  Removed: {table_comp['removed_count']}")
                print(f"  Modified: {table_comp['modified_count']}")

        return comparison

