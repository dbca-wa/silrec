"""Tests for processed-geometry display-field enrichment.

Run with debug-toolbar disabled (it is enabled by SHOW_DEBUG_TOOLBAR in .env):

    SHOW_DEBUG_TOOLBAR=False python manage.py test \\
        silrec.components.forest_blocks.tests --keepdb

The suite requires PostGIS. ``--keepdb`` is recommended because the migration
graph references models that no longer resolve on a fresh database.
"""

import json
from datetime import datetime

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from django.test import TestCase

from silrec.components.forest_blocks.models import (
    Cohort,
    Compartments,
    Operation,
)
from silrec.components.lookups.models import (
    ObjectiveLkp,
    RegenerationMethodsLkp,
)
from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger


def make_merger(proposal_id=1):
    """Build a ShapefileSliversMerger without running __init__ (no shapefile)."""
    merger = ShapefileSliversMerger.__new__(ShapefileSliversMerger)
    merger.proposal_id = proposal_id
    return merger


class EnrichGdfWithDisplayFieldsTests(TestCase):
    """Tests for the processed-geometry display-field enrichment.

    These guard the map "Feature Details" popup data and, importantly, assert
    that enrichment is additive/JSON-safe so shapefile processing is unaffected.
    """

    @classmethod
    def setUpTestData(cls):
        cls.regen = RegenerationMethodsLkp.objects.create(
            regen_method='ZZ', description='test'
        )
        cls.objective = ObjectiveLkp.objects.create(
            obj_code='TEST-OBJ', description='test objective'
        )
        cls.operation = Operation.objects.create(
            fea_id='ABC1234',
        )
        cls.cohort = Cohort.objects.create(
            obj_code='TEST-OBJ',
            species='  J  ',
            op_id=cls.operation.op_id,
            op_date=datetime(2011, 12, 15),
            regen_date=datetime(2013, 11, 15),
            complete_date=datetime(2014, 1, 1),
            target_ba_m2ha=12.5,
            resid_ba_m2ha=0.0,
            target_spha=None,
            resid_spha=5.0,
            regen_method=cls.regen,
        )
        cls.compartment = Compartments.objects.create(
            compartment='TST01',
            block='ABBA',
            district='S.W. CAPES',
            region='SOUTHWEST',
        )

    def _gdf(self, rows):
        return gpd.GeoDataFrame(
            {
                'poly_id_new': [r.get('poly_id_new') for r in rows],
                'cht_id_new': [r.get('cht_id_new') for r in rows],
                'compartment': [r.get('compartment') for r in rows],
                'area_ha': [r.get('area_ha', 1.0) for r in rows],
                'geometry': [Point(i, i) for i in range(len(rows))],
            },
            crs='EPSG:4326',
        )

    def test_joins_cohort_and_compartment_attributes(self):
        gdf = self._gdf(
            [
                {
                    'poly_id_new': 1,
                    'cht_id_new': self.cohort.cohort_id,
                    'compartment': 'TST01',
                }
            ]
        )

        out = make_merger().enrich_gdf_with_display_fields(gdf)
        row = out.iloc[0]

        self.assertEqual(row['fea_id'], 'ABC1234')
        self.assertEqual(row['obj_code'], 'TEST-OBJ')
        self.assertEqual(row['species'], 'J')
        self.assertEqual(row['target_ba_m2ha'], 12.5)
        self.assertEqual(row['resid_ba_m2ha'], 0.0)
        self.assertEqual(row['resid_spha'], 5.0)
        self.assertEqual(row['block'], 'ABBA')
        self.assertEqual(row['district'], 'S.W. CAPES')
        self.assertEqual(row['region'], 'SOUTHWEST')
        # Legacy popup keys mirroring the raw shapefile schema.
        self.assertEqual(row['Block'], 'ABBA')
        self.assertEqual(row['Compno'], 'TST01')
        self.assertEqual(row['Region'], 'SOUTHWEST')
        self.assertEqual(row['Area'], 1.0)

    def test_missing_lookups_become_none_not_nan(self):
        gdf = self._gdf(
            [
                {
                    'poly_id_new': 2,
                    'cht_id_new': 999999999,
                    'compartment': 'NOPE',
                }
            ]
        )

        out = make_merger().enrich_gdf_with_display_fields(gdf)
        row = out.iloc[0]

        for field in ('fea_id', 'obj_code', 'species', 'block', 'district', 'region'):
            self.assertIsNone(
                row[field], f'{field} should be None for unmatched rows'
            )

    def test_output_is_json_serializable(self):
        gdf = self._gdf(
            [
                {
                    'poly_id_new': 1,
                    'cht_id_new': self.cohort.cohort_id,
                    'compartment': 'TST01',
                }
            ]
        )

        out = make_merger().enrich_gdf_with_display_fields(gdf)

        # geopandas to_json() is what the processing pipeline ultimately uses.
        geojson = out.to_json()
        data = json.loads(geojson)
        props = data['features'][0]['properties']

        self.assertEqual(props['fea_id'], 'ABC1234')
        self.assertEqual(props['obj_code'], 'TEST-OBJ')
        self.assertEqual(props['Block'], 'ABBA')
        self.assertEqual(props['Compno'], 'TST01')
        # Dates must be strings, never pandas Timestamps.
        self.assertIsInstance(props['op_date'], str)

    def test_enrichment_does_not_drop_or_reorder_rows(self):
        rows = [
            {
                'poly_id_new': 1,
                'cht_id_new': self.cohort.cohort_id,
                'compartment': 'TST01',
            },
            {'poly_id_new': 2, 'cht_id_new': 0, 'compartment': 'NOPE'},
            {'poly_id_new': 3, 'cht_id_new': 0, 'compartment': 'TST01'},
        ]
        gdf = self._gdf(rows)

        out = make_merger().enrich_gdf_with_display_fields(gdf)

        self.assertEqual(len(out), len(rows))
        self.assertEqual(list(out['poly_id_new']), [1, 2, 3])

    def test_empty_gdf_returned_unchanged(self):
        gdf = self._gdf([])
        out = make_merger().enrich_gdf_with_display_fields(gdf)

        self.assertEqual(len(out), 0)
        self.assertNotIn('fea_id', out.columns)

    def test_none_gdf_returned_unchanged(self):
        self.assertIsNone(
            make_merger().enrich_gdf_with_display_fields(None)
        )

    def test_failure_is_swallowed_and_gdf_preserved(self):
        """Enrichment must never break processing: on error return the input."""
        gdf = self._gdf(
            [
                {
                    'poly_id_new': 1,
                    'cht_id_new': self.cohort.cohort_id,
                    'compartment': 'TST01',
                }
            ]
        )
        original_columns = list(gdf.columns)

        merger = make_merger()
        # Force the lookup to fail.
        merger.COHORT_DISPLAY_FIELDS = ['fea_id']

        from unittest import mock

        with mock.patch(
            'silrec.utils.shapefile_silvers_merger.Cohort.objects.filter',
            side_effect=Exception('boom'),
        ):
            out = merger.enrich_gdf_with_display_fields(gdf)

        # Returned object is the (unmodified) input gdf.
        self.assertEqual(list(out.columns), original_columns)
        self.assertEqual(len(out), 1)


class PrepProposalDataTests(TestCase):
    """prep_proposal_data should enrich both per-iteration and combined gdfs."""

    @classmethod
    def setUpTestData(cls):
        cls.regen = RegenerationMethodsLkp.objects.create(
            regen_method='YY', description='test'
        )
        cls.objective = ObjectiveLkp.objects.create(
            obj_code='PREP-OBJ', description='test objective'
        )
        cls.operation = Operation.objects.create(fea_id='XYZ9999')
        cls.cohort = Cohort.objects.create(
            obj_code='PREP-OBJ',
            species='K',
            op_id=cls.operation.op_id,
            op_date=datetime(2012, 1, 1),
            regen_method=cls.regen,
        )
        Compartments.objects.create(
            compartment='ZZZ01', block='ZZB', district='D1', region='R1'
        )

    def _gdf(self):
        return gpd.GeoDataFrame(
            {
                'poly_id_new': [1],
                'cht_id_new': [self.cohort.cohort_id],
                'compartment': ['ZZZ01'],
                'area_ha': [2.5],
                'geometry': [Point(0, 0)],
            },
            crs='EPSG:4326',
        )

    def test_combined_and_iteration_features_are_enriched(self):
        combined = self._gdf()
        iteration = self._gdf().assign(iter_seq=1)
        list_state = [
            {'GDF_RESULT_COMBINED': combined},
            {
                'GDF_HIST': self._gdf(),
                'GDF_SINGLE': self._gdf(),
                'GDF_RESULT': iteration,
                'GDF_CHT_INIT': pd.DataFrame({'a': [1]}),
                'GDF_CHT_NEW': pd.DataFrame({'a': [1]}),
            },
        ]

        merger = make_merger()
        geom_data = merger.prep_proposal_data(list_state)

        # Combined gdf is enriched in place for geojson_data_processed.
        self.assertIn('fea_id', list_state[0]['GDF_RESULT_COMBINED'].columns)

        # Per-iteration geojson carries the display fields.
        self.assertIn('geometry_1', geom_data)
        props = geom_data['geometry_1']['features'][0]['properties']
        self.assertEqual(props['fea_id'], 'XYZ9999')
        self.assertEqual(props['obj_code'], 'PREP-OBJ')
        self.assertEqual(props['block'], 'ZZB')
