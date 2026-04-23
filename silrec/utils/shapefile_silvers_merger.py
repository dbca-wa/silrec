from django.conf import settings
from django.db import models, transaction, IntegrityError, connection
from django.contrib.auth import get_user_model
from django.utils import timezone

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.ops import unary_union, polygonize
from shapely import from_wkb

import json
import os
from copy import deepcopy

import reversion

#from silrec.utils.plot_utils import plot_gdf as plot
#from silrec.utils.plot_utils import plot_overlay, plot_multi
#from silrec.utils.plot_canvas import create_tabbed_charts
from silrec.utils.sliver_merge import find_and_merge
from silrec.utils.sliver_test1 import identify_slivers

from silrec.utils.write_polygons_to_db import write_polygons_to_db
from silrec.utils.write_cohort_to_db import write_cohort_to_db, save_cht_new_to_db

from silrec.components.forest_blocks.models import Polygon, Cohort, AssignChtToPly
from silrec.components.proposals.models import Proposal
from silrec.utils.create_audit_log import RequestMetrics, AuditLogger

import logging
logger = logging.getLogger(__name__)

User = get_user_model()

class ShapefileSliversMerger():
    '''
    import geopandas as gpd
    from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger
    from silrec.utils.create_temp_tables import drop_prod_tables_django

    gdf_shp_16 = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')


    drop_prod_tables_django()
    !PGPASSWORD='dev123' pg_restore -h localhost -p 5432 -U dev -d silrec_test3 silrec_3tables_14Mar2026.dump
    ssm = ShapefileSliversMerger(proposal_id=1, gdf_shpfile=gdf_shp_16, threshold=5, user_id=1)
    list_state = ssm.create_gdf()

    print(len(list_state[0]['GDF_RESULT_COMBINED']))
    plot_multi([list_state[0]['GDF_SHP'], list_state[0]['GDF_HIST'], list_state[0]['GDF_RESULT_COMBINED']])

    '''
    def __init__(self, proposal_id, gdf_shpfile=None, threshold=None, user_id=None):
        self.proposal_id = proposal_id
        self.gdf_shpfile = self.get_shapefile(gdf_shpfile)
        self.threshold = threshold
        self.user_id = user_id

    def get_shapefile(self, gdf_shpfile):
        if gdf_shpfile is None:
            try:
                p = Proposal.objects.get(id=self.proposal_id)
                if p.geojson_shpfile_to_gdf is not None:
                    return p.geojson_shpfile_to_gdf.to_crs(settings.CRS_GDA94)
                raise Exception(f'There is no Shapefile associated with this Proposal {self.proposal_id}')
            except Proposal.DoesNotExist as pe:
                raise Proposal.DoesNotExist(f'{pe}. Proposal ID {self.proposal_id}')
            except Exception as e:
                raise Exception(f'{e}')

        return gdf_shpfile

    def get_polygons_gdf(self, gdf, table_name, proposal_id, sql=None):
        ''' Get intersecting polygons from forest_blocks.polygon - intersecting with the given base polygon

            Returns --> SQL query result as gdf
        '''

        if not sql:
            srid = 'SRID=' + settings.CRS_GDA94.split(':')[1] + '; '
            combined_geometry = unary_union(gdf['geometry'])
            base_polygon_wkt = srid + combined_geometry.wkt

            sql = f'''SELECT
                    ph.polygon_id,
                    ph.name,
                    ph.area_ha,
                    ph.compartment,
                    ph.sp_code,
                    ph.geom
                FROM {table_name} AS ph
                WHERE ph.zclosed IS NULL
                AND (
                    ST_Overlaps(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                    OR ST_Contains(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                    OR ST_Within(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                    OR ST_Crosses(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                )
                ;'''

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        geom_col = 'geom'
        data_dict = {col: [] for col in columns}
        for row in rows:
            for i, col in enumerate(columns):
                data_dict[col].append(row[i])

        data_dict[geom_col] = [from_wkb(g) if g is not None else None for g in data_dict[geom_col]]

        gdf = gpd.GeoDataFrame(data_dict, geometry=geom_col, crs=settings.CRS_GDA94)

        gdf['polygon_id'] = pd.to_numeric(gdf['polygon_id'], errors='coerce').astype(int)

        gdf['poly_type'] = 'HIST'
        gdf['iter_seq'] = 1
        gdf['proposal_id'] = proposal_id

        return gdf.explode()

    def get_base_polygon_gdf(self, gdf_base, gdf_common_boundary):
        ''' returns the equiv. of gdf_single, but the one after
            historical polygon intersection and subsequent splitting
            to form new polygons

            --> Returns the 'new split' base polygon
        '''
        centroids_gdf1 = gdf_base.geometry.representative_point()
        centroids_df = gpd.GeoDataFrame(geometry=centroids_gdf1)

        if 'index_right' in gdf_common_boundary.columns:
            gdf_common_boundary.drop(['index_right'], axis=1, inplace=True)

        gdf = gpd.sjoin(gdf_common_boundary, centroids_df, how="inner", predicate="intersects")
        gdf['poly_type'] = 'BASE'
        gdf['polygon_id'] = gdf['polygon_id'] if 'polygon_id' in gdf.columns else 0
        gdf['proposal_id'] = self.proposal_id

        return gdf.iloc[[0]]

    def merge_touching(self, gdf, buffer_distance=0.0001):
        '''
        Use small buffer to ensure boundaries connect properly,
        then merge and remove buffer

        merged_gdf = merge_touching(gdf)
        '''
        # Apply small buffer to ensure connections
        buffered = gdf.geometry.buffer(buffer_distance)

        # Merge buffered geometries
        merged_buffered = unary_union(buffered)

        # Remove the buffer
        merged_clean = merged_buffered.buffer(-buffer_distance)

        return gpd.GeoDataFrame([1], geometry=[merged_clean], crs=gdf.crs)

    def create_gdf(self, savepoint_callback=None):
        '''
        Main processing method that creates the merged GeoDataFrames
        '''

        #logger.info(self.proposal_id, self.gdf_shpfile, self.threshold, self.user_id)
        idx_count = 0
        gdf_shpfile = self.gdf_shpfile.copy()
        list_state = []

        # SET Init history and Shapefile to list_state
        gdf_hist = self.get_polygons_gdf(self.gdf_shpfile, 'polygon', self.proposal_id)
        polygon_ids_hist = gdf_hist.polygon_id.to_list()
        assignments = AssignChtToPly.objects.filter(polygon_id__in=polygon_ids_hist).values('cohort_id', 'cht2ply_id')
        cohort_ids_hist = [a['cohort_id'] for a in assignments]
        cht2ply_ids_hist = [a['cht2ply_id'] for a in assignments]

        # initialise store
        list_state.append({
            "gdf_hist".upper(): gdf_hist.copy(),
            "gdf_shp".upper(): self.gdf_shpfile.copy(),
        })

        proposal = Proposal.objects.get(id=self.proposal_id)
        user = User.objects.get(id=self.user_id)
        self.request_metrics = RequestMetrics.objects.create(proposal=proposal, user=user)

        # Process each polygon in the shapefile
        #for index, row in self.gdf_shpfile[:2].iterrows():
        for index, row in self.gdf_shpfile.iterrows():
            idx_count += 1
            logger.info('****************************************************************************************')
            logger.info(f'                                 Polygon {idx_count}')
            logger.info('****************************************************************************************')

            try:
                # Start a transaction with reversion
                with transaction.atomic():
                    with reversion.create_revision() as revision:
                        # Create a single polygon GeoDataFrame
                        self.gdf_single = gpd.GeoDataFrame([row], geometry=[row.geometry], crs=settings.CRS_GDA94)
                        self.gdf_single = self.set_data(self.gdf_single, poly_type='BASE')

                        target_ba = float(self.gdf_single.iloc[0].target_ba_)
                        obj_code = self.gdf_single.iloc[0].obj_code
                        op_id = 1
                        year = 2024
                        regen_method = ' %'  # non-null FK req'd

                        # Create cohort and pass revision
                        cohort_id = write_cohort_to_db(
                            obj_code, op_id, year, target_ba, regen_method,
                            self.request_metrics, idx_count, revision
                        )

                        # Get intersecting historical polygons
                        gdf_hist = self.get_polygons_gdf(self.gdf_single, 'polygon', self.proposal_id)

                        # Rename columns for consistency
                        gdf_hist.rename(columns={'geom': 'geometry'}, inplace=True)
                        gdf_hist.set_geometry('geometry', inplace=True)
                        gdf_hist.set_crs(settings.CRS_GDA94, inplace=True)

                        # Process cookie cut
                        gdf_result = self.process_cookie_cut(gdf_hist)

                        # Assemble result with cohort data
                        gdf_result = self.assemble_gdf_result(gdf_result, gdf_hist, cohort_id, op_id, idx_count, revision)
                        gdf_result['poly_id_new'] = pd.to_numeric(gdf_result['poly_id_new'], errors='coerce').fillna(0).astype(int)

                        # Get initial cohort data
                        gdf_cht_init, cohort_gdf_init = self.merge_cohort_data_init(gdf_result, gdf_hist)
                        gdf_cht_init['polygon_id'] = pd.to_numeric(gdf_cht_init['polygon_id'], errors='coerce').fillna(0).astype(int)

                        # Get new cohort data
                        gdf_cht_new = self.merge_cohort_data_new(gdf_result, gdf_hist, cohort_gdf_init, cohort_id, op_id)

                        # Save new cohort assignments with revision
                        save_cht_new_to_db(gdf_cht_new, self.request_metrics, idx_count, revision)

                        # Store state
                        list_state = self.set_gdf_store(idx_count, list_state, gdf_hist, gdf_result, gdf_cht_init, gdf_cht_new)

                        # Planar enforcement check for this iteration
                        iter_gdf = list_state[idx_count]['GDF_RESULT']
                        is_planar, fixed_gdf = self.check_planar_enforcement(iter_gdf, f'iteration {idx_count}', fix_overlaps=True)
                        if fixed_gdf is not None:
                            list_state[idx_count]['GDF_RESULT'] = fixed_gdf
                            logger.info(f"Updated iteration {idx_count} with planar-fixed geometries")

                        # Set reversion comment
                        reversion.set_comment(f'Shapefile processing iteration {idx_count} for proposal {self.proposal_id}')

            except Exception as e:
                # Something went wrong in this iteration
                logger.error(f"Error in iteration {idx_count}: {str(e)}")
                # Re-raise the exception to stop processing
                raise

        # Add combined gdf_result's to list_state
        gdf_result_combined = self.get_gdf_result_combined(list_state)
        list_state[0].update({'GDF_RESULT_COMBINED': gdf_result_combined})

        # Planar enforcement check for final combined result (i=0)
        is_planar_final, fixed_gdf_final = self.check_planar_enforcement(
            list_state[0]['GDF_RESULT_COMBINED'],
            'final (i=0)',
            fix_overlaps=True
        )
        if fixed_gdf_final is not None:
            list_state[0]['GDF_RESULT_COMBINED'] = fixed_gdf_final
            logger.info("Updated final combined result with planar-fixed geometries")

        #import ipdb; ipdb.set_trace()
        return list_state

    def set_gdf_store(self, idx_count, list_state, gdf_hist, gdf_result, gdf_cht_init, gdf_cht_new):
        gdf_cht_init = gdf_cht_init.copy()

        self.gdf_single['iter_seq'] = idx_count
        gdf_result['iter_seq'] = idx_count
        gdf_cht_init['iter_seq'] = idx_count
        gdf_cht_new['iter_seq'] = idx_count

        # add column identifying store type
        gdf_hist['state'] = "gdf_hist".upper()
        self.gdf_single['state'] = "gdf_single".upper()
        gdf_result['state'] = "gdf_result".upper()
        gdf_cht_init['state'] = "gdf_cht_init".upper()
        gdf_cht_new['state'] = "gdf_cht_new".upper()

        list_state.append({
            "gdf_hist".upper(): gdf_hist.copy(),
            "gdf_single".upper(): self.gdf_single.copy(),
            "gdf_result".upper(): gdf_result.copy(),
            "gdf_cht_init".upper(): gdf_cht_init.copy(),
            "gdf_cht_new".upper(): gdf_cht_new.copy(),
        })

        return list_state

    def process_cookie_cut(self, gdf_hist):
        '''
        Performs the (shapefile) polygon overlay onto historical (current) polygons nd
        cookie-cut's the intersections. Then absorbs/merges the slivers for the
        given area/length threshold
        '''
        # Determine which geometries in polygons geodataframe (hist) intersect with any geometry in gdf_single
        # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
        intersects_mask_single = gdf_hist.geometry.intersects(self.gdf_shpfile.unary_union)
        gdf_polygons_intersecting_single = gdf_hist[intersects_mask_single]

# non overlapping overlayed geometries (creates independent partitioned geometries)
        self.gdf_polygons_partitioned = gpd.overlay(self.gdf_single[['geometry']], gdf_polygons_intersecting_single, how='union', keep_geom_type=True)
        self.gdf_polygons_partitioned = self.gdf_polygons_partitioned[self.gdf_polygons_partitioned.area>1] # drop tiny areas (> 1 sqm)
        self.gdf_polygons_partitioned = self.gdf_polygons_partitioned.explode(index_parts=False).explode(index_parts=False)
        self.gdf_polygons_partitioned.reset_index(inplace=True)

        base_polygon = self.get_base_polygon_gdf(self.gdf_single, self.gdf_polygons_partitioned)[['geometry']]
        base_polygon['poly_type'] = 'BASE'

        # extract the land slivers
        self.threshold = self.threshold if self.threshold else settings.SLIVER_AREALENGTH_THRESHOLD
        gdf_polys_exploded = self.gdf_polygons_partitioned.copy()
        gdf_slivers = identify_slivers(gdf_polys_exploded, base_polygon, sliver_threshold=self.threshold)
        gdf_slivers['poly_type'] = 'SLVR'
        mask = gdf_polys_exploded.geometry.area / gdf_polys_exploded.geometry.length < self.threshold
        gdf_excl_slivers = gdf_polys_exploded[~(mask)]
        gdf_slivers_plus_base = gpd.GeoDataFrame(pd.concat([gdf_slivers, base_polygon], ignore_index=True))

        # re-merge land slivers to base_polygon and create poly_type column
        gdf_excl_slivers_plus_base = gpd.overlay(self.gdf_polygons_partitioned, gdf_slivers_plus_base, how='difference', keep_geom_type=True)
        gdf_excl_slivers_plus_base['poly_type'] = 'HIST'
        gdf_slivers_merged = gdf_slivers_plus_base.dissolve()
        gdf_slivers_merged['poly_type'] = 'BASE'
        gdf_slivers_merged['polygon_id'] = 0
        gdf_slivers_merged['proposal_id'] = self.proposal_id

        # re-merge merged base_polygon with remaining cookie-cut and hist polygons
        gdf_result = gpd.GeoDataFrame(pd.concat([gdf_excl_slivers_plus_base, gdf_slivers_merged], ignore_index=True))
        gdf_result = gdf_result[gdf_result.area>1] # drop tiny areas  (> 1 sqm)

        return gdf_result

    def get_gdf_result_combined(self, list_state):
        # Concatenate the two GeoDataFrames
        gdf_result_combined = pd.concat([d['GDF_RESULT'] for d in list_state[1:]], ignore_index=True)

        # Sort by iter_seq descending so that the highest value comes first for each poly_id_new
        gdf_result_combined_sorted = gdf_result_combined.sort_values('iter_seq', ascending=False)

        # Drop duplicates based on poly_id_new, keeping the first (which has the max iter_seq)
        gdf_result_combined_deduplicated = gdf_result_combined_sorted.drop_duplicates(subset='poly_id_new', keep='first')

        return gdf_result_combined_deduplicated

    def check_planar_enforcement(self, gdf, iteration_label='unknown', fix_overlaps=True):
        """
        Check for planar geometry enforcement (no overlapping polygons).

        Args:
            gdf: GeoDataFrame to check
            iteration_label: Label for logging (e.g., 'iteration 1' or 'final')
            fix_overlaps: If True, fix overlapping polygons by merging them

        Returns:
            tuple: (is_planar: bool, fixed_gdf: GeoDataFrame or None)
        """
        if gdf is None or len(gdf) == 0:
            logger.warning(f"Empty GeoDataFrame passed to planar check at {iteration_label}")
            return True, None

        is_planar = True
        fixed_gdf = None

        # Check for invalid geometries first
        invalid_geoms = gdf[~gdf.is_valid]
        if len(invalid_geoms) > 0:
            logger.warning(f"Found {len(invalid_geoms)} invalid geometries at {iteration_label}")
            is_planar = False

            if fix_overlaps:
                logger.info(f"Fixing invalid geometries at {iteration_label} using buffer(0)")
                gdf = gdf.copy()
                gdf['geometry'] = gdf['geometry'].buffer(0)
                fixed_gdf = gdf
                is_planar = True

        # Check for overlapping geometries
        if len(gdf) > 1:
            overlaps = []
            geoms = gdf['geometry'].tolist()
            poly_ids = gdf['poly_id_new'].tolist() if 'poly_id_new' in gdf.columns else range(len(gdf))

            for i in range(len(geoms)):
                for j in range(i + 1, len(geoms)):
                    if geoms[i].intersects(geoms[j]):
                        # Check if it's a proper intersection (not just touching at edge/point)
                        intersection = geoms[i].intersection(geoms[j])
                        if intersection.area > 0.001:  # Ignore tiny intersections
                            overlaps.append((poly_ids[i], poly_ids[j], intersection.area))

            if overlaps:
                is_planar = False
                logger.warning(f"Found {len(overlaps)} overlapping polygon pairs at {iteration_label}:")
                for poly1, poly2, area in overlaps[:5]:  # Log first 5
                    logger.warning(f"  Overlap: poly_id_new {poly1} <-> {poly2}, area: {area:.2f} sqm")
                if len(overlaps) > 5:
                    logger.warning(f"  ... and {len(overlaps) - 5} more overlaps")

                if fix_overlaps:
                    logger.info(f"Fixing overlaps at {iteration_label} using unary_union")
                    gdf = self._fix_overlapping_polygons(gdf)
                    fixed_gdf = gdf
                    is_planar = True

        if is_planar:
            logger.info(f"Planar enforcement passed at {iteration_label}: {len(gdf)} polygons")

        return is_planar, fixed_gdf

    def _fix_overlapping_polygons(self, gdf):
        """
        Fix overlapping polygons by unioning overlapping areas.
        Uses the largest polygon to absorb overlaps.
        """
        if len(gdf) <= 1:
            return gdf

        gdf = gdf.copy().reset_index(drop=True)
        geoms = gdf['geometry'].tolist()

        merged_geoms = []
        used = set()

        for i in range(len(geoms)):
            if i in used:
                continue

            current_geom = geoms[i]
            used.add(i)

            for j in range(i + 1, len(geoms)):
                if j in used:
                    continue

                if current_geom.intersects(geoms[j]):
                    intersection = current_geom.intersection(geoms[j])
                    if intersection.area > 0.001:
                        current_geom = current_geom.union(geoms[j])
                        used.add(j)

            merged_geoms.append(current_geom)

        gdf['geometry'] = merged_geoms

        return gdf

    def prep_proposal_data(self, list_state):
        '''
            Creates Data Structure for input to model Proposal
        '''
        geom_data = {}
        for i in range(1, len(list_state)): # ignore index 0 - base data
            gdf_hist = list_state[i]['GDF_HIST']
            gdf_single = list_state[i]['GDF_SINGLE']
            gdf_result = list_state[i]['GDF_RESULT']
            gdf_cht_init = list_state[i]['GDF_CHT_INIT']
            gdf_cht_new = list_state[i]['GDF_CHT_NEW']

            geojson = json.loads(gdf_result.to_crs(settings.CRS).to_json())
            geojson['cht_init'] = gdf_cht_init.to_json()
            geojson['cht_new'] = gdf_cht_new.to_json()

            geom_data.update({f'geometry_{i}': geojson})

        return geom_data

    def set_data(self, gdf, polygon_id=0, poly_type=None):
        gdf['proposal_id'] = self.proposal_id
        gdf['polygon_id'] = polygon_id if 'polygon_id' not in gdf else gdf['polygon_id'].fillna(polygon_id)
        if poly_type == 'SLVR':
            try:
                gdf['poly_type'] = gdf['poly_type'].fillna('SLVR')
            except:
                gdf['poly_type'] = 'SLVR'

        elif poly_type == 'BASE':
            gdf['poly_type'] = 'HIST'
            base_polygon = self.get_base_polygon_gdf(self.gdf_single, self.gdf_shpfile)
            if not base_polygon.empty:
                gdf.at[base_polygon.iloc[0].name, 'poly_type'] = 'BASE' # 'BASE'

        else:
            logger.error(f'poly_type {poly_type} not recognised')

        return gdf

    @property
    def gdf_result_filtered(self):
        iters = [int(item) for item in self.gdf_merge_store.iter_seq.unique() if not (isinstance(item, float) and np.isnan(item))]
        return self.gdf_merge_store[(self.gdf_merge_store.state=='GDF_RESULT_FILTERED') & (self.gdf_merge_store.iter_seq==max(iters))]

#    def plot_canvas(self):
#        '''
#        import geopandas as gpd
#        from silrec.utils.shapefile_silvers_merger3 import ShapefileSliversMerger
#
#        gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
#        gdf_shp.to_crs('EPSG:28350', inplace=True)
#        ssm = ShapefileSliversMerger(gdf_shp, proposal_id=1)
#
#        gdf_merge_store = ssm.create_gdf()
#        ssm.plot_canvas()
#
#        '''
#        iters = [int(item) for item in self.gdf_merge_store.iter_seq.unique() if not (isinstance(item, float) and np.isnan(item))]
#        iters.insert(0, 0)
#        states = [item for item in self.gdf_merge_store.state.unique() if not (isinstance(item, float) and np.isnan(item))]
#
#        gdf_iter_list = []
#        chart_titles_list = []
#        for it in iters[:3]:
#            gdf_state_list = []
#            chart_titles = []
#            if it == 0:
#                # Plot Summary on first Tab
#                gdf_state_list.append(self.gdf_shpfile)
#                gdf_state_list.append(self.gdf_hist_polygons_total)
#                gdf_state_list.append(self.gdf_result_filtered)
#                chart_titles.append(f'Shpfile: Polys {len(self.gdf_shpfile)}, Area_HA {round(self.gdf_shpfile.area.sum()/10000, 2)}')
#                chart_titles.append(f'Hist: Polys {len(self.gdf_hist_polygons_total)}, Area_HA {round(self.gdf_hist_polygons_total.area.sum()/10000, 2)}')
#                chart_titles.append(f'Result: Polys {len(self.gdf_result_filtered)}, Area_HA {round(self.gdf_result_filtered.area.sum()/10000, 2)}')
#
#            else:
#                for state in states:
#                    gdf = self.gdf_merge_store[(self.gdf_merge_store.state==state) & (self.gdf_merge_store.iter_seq==it)]
#                    gdf['colour'] = gdf['poly_type'].apply(lambda x: 'grey' if x=='BASE' else ('green' if x=='CUT' else ('yellow' if x=='SLVR' else 'BLUE')))
#                    gdf_state_list.append(gdf)
#                    chart_titles.append(f'{state} - Polygons {len(gdf)}, Area_HA {round(gdf.area.sum()/10000, 2)}')
#
#            gdf_iter_list.append(gdf_state_list)
#            chart_titles_list.append(chart_titles)
#
#        create_tabbed_charts(*gdf_iter_list, chart_titles=chart_titles_list)

    def classify_polygons(self, gdf_result, gdf_single, tolerance=0.95):
        """
        Classify polygons in gdf_result based on their spatial relationship with gdf_single
        with area-based tolerance.
        i.e. set gdf_result.poly_type = 'BASE' or 'CUT', with area tolerance

        Parameters:
        gdf_result: GeoDataFrame with polygons to classify
        gdf_single: GeoDataFrame with reference polygon(s)
        tolerance: float (0-1), minimum proportion of area that must be inside gdf_single
                to be classified as 'BASE'. Default 0.95 (95%)

        Returns:
        GeoDataFrame with added 'poly_type' column
        """

        # Create a unified geometry from gdf_single for efficient spatial operations
        if len(gdf_single) > 0:
            hist_union = gdf_single.unary_union
        else:
            # If gdf_single is empty, all polygons are 'CUT'
            gdf_result = gdf_result.copy()
            gdf_result['poly_type'] = 'CUT'
            return gdf_result

        # Initialize the result column
        gdf_result = gdf_result.copy()
        poly_types = []

        for geom in gdf_result.geometry:
            if geom is None or geom.is_empty:
                poly_types.append('CUT')
                continue

            # Calculate the intersection area
            try:
                intersection = geom.intersection(hist_union)
                if intersection.is_empty:
                    # No intersection at all
                    area_ratio = 0.0
                else:
                    # Calculate ratio of intersection area to original area
                    area_ratio = intersection.area / geom.area

                # Classify based on area ratio
                if area_ratio >= tolerance:
                    poly_types.append('BASE')
                else:
                    poly_types.append('CUT')

            except Exception as e:
                # Handle any geometric operation errors
                logger.error(f"Error processing geometry: {e}")
                poly_types.append('CUT')

        gdf_result['poly_type'] = poly_types
        gdf_result['area_ratio'] = [intersection.area / geom.area if geom and not geom.is_empty else 0.0
        for geom, intersection in zip(gdf_result.geometry,
            [g.intersection(hist_union) for g in gdf_result.geometry])]

        return gdf_result

    def add_cht_id_to_gdf_sql(self, gdf_result):
        ''' Query the DB table assign_cht_to_ply for ply_id's, cht_id's
        '''
        # Get polygon_ids
        polygon_ids = gdf_result['polygon_id'].tolist()

        # Query using Django ORM with proper error handling
        try:
            # Check if we're in a transaction and it's valid
            from django.db import connection
            if connection.in_atomic_block and not connection.needs_rollback:
                queryset = AssignChtToPly.objects.filter(
                    polygon_id__in=polygon_ids,
                    status_current=True
                ).values('polygon_id', 'cohort_id')

                # Create mapping dictionary
                cohort_mapping = {item['polygon_id']: item['cohort_id'] for item in queryset}

                # Apply to GeoDataFrame
                gdf_result['cht_id_cur'] = gdf_result['polygon_id'].map(cohort_mapping).fillna(1).astype(int)
#            else:
#                # Transaction is in a bad state, use SQLAlchemy as fallback
#                logger.warning("Transaction in bad state, using SQLAlchemy fallback")
#                return self.add_cht_id_to_gdf_sql_alc(gdf_result)

        except Exception as e:
            logger.error(f"Unexpected error creating cohort record: {e}")
            # Try SQLAlchemy as fallback
            return self.add_cht_id_to_gdf_sql_alc(gdf_result)

        return gdf_result

#    def add_cht_id_to_gdf_sql_alc(self, gdf_result):
#        ''' Uses SqlAlchemy - Query the DB table assign_cht_to_ply for ply_id's, cht_id's
#        '''
#
#        polygon_ids = gdf_result['polygon_id'].tolist()
#
#        # Using text() for safe parameterized queries
#        query = text("""
#            SELECT polygon_id, cohort_id
#            FROM assign_cht_to_ply
#            WHERE polygon_id = ANY(:polygon_ids) AND status_current = True
#        """)
#
#        with self.conn_engine.connect() as conn:
#            result = conn.execute(query, {'polygon_ids': polygon_ids})
#            cohort_mapping = {row[0]: row[1] for row in result}
#
#        gdf_result['cht_id_cur'] = gdf_result['polygon_id'].map(cohort_mapping).fillna(1).astype(int)
#
#        return gdf_result

    def merge_cohort_data_init(self, gdf_result, gdf_hist):
        """
        Query DB for cohort data.
        Namely, from 'polygon - assign_cht_to_ply - cohort' triple using SQL JOIN and merge with gdf
        """

        cols = ['polygon_id', 'area_ha_orig', 'poly_type', 'cht_type', 'cht_id_cur', 'iter_seq', 'proposal_id']
        gdf_cht_init = gdf_result[gdf_result.polygon_id==gdf_result.poly_id_new][cols].copy()

        if gdf_cht_init.empty:
            return gdf_result

        polygon_ids = gdf_hist.polygon_id.to_list()
        polygon_ids = list(set(polygon_ids)) if polygon_ids else [0]

        cohort_ids = gdf_result.cht_id_cur.to_list()
        cohort_ids = list(set(cohort_ids)) if cohort_ids else [0]
        if len(cohort_ids) == 0:
            return None

        try:
            query = f"""
                SELECT
                    tp.polygon_id,
                    tp.name,
                    tp.area_ha,
                    tp.compartment,
                    tp.sp_code,
                    tactp.cht2ply_id,
                    tactp.polygon_id as assign_polygon_id,
                    tactp.cohort_id as assign_cohort_id,
                    tactp.status_current,
                    tc.cohort_id,
                    tc.obj_code,
                    tc.op_id,
                    tc.complete_date,
                    tc.target_ba_m2ha
                FROM polygon tp
                LEFT JOIN assign_cht_to_ply tactp ON tp.polygon_id = tactp.polygon_id
                LEFT JOIN cohort tc ON tactp.cohort_id = tc.cohort_id
                WHERE tactp.cohort_id=ANY(ARRAY[{','.join(map(str, cohort_ids))}]) AND tactp.status_current=True;
            """

            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                cohort_gdf_init = pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f'{e}')
            pass

        # Merge with original GeoDataFrame
        gdf_cht_init = gdf_cht_init.merge(
            cohort_gdf_init,
            left_on='cht_id_cur',
            right_on='cohort_id',
            how='left'
        )

        # Drop spurious columns created by merge
        if 'obj_code' not in gdf_cht_init.columns:
            gdf_cht_init = gdf_cht_init.drop('obj_code_x', axis=1)
            gdf_cht_init = gdf_cht_init.rename(columns={'obj_code_y': 'obj_code'})

        # Drop spurious columns created by merge
        if 'polygon_id' not in gdf_cht_init.columns:
            gdf_cht_init = gdf_cht_init.drop('polygon_id_x', axis=1)
            gdf_cht_init = gdf_cht_init.rename(columns={'polygon_id_y': 'polygon_id'})

        # Strip blank spaces from obj_code
        gdf_cht_init['obj_code'] = gdf_cht_init['obj_code'].str.strip()

        cols_reqd = ['cohort_id', 'polygon_id', 'cht2ply_id', 'name', 'area_ha_orig', 'obj_code', 'complete_date', 'target_ba_m2ha', 'op_id', 'status_current']
        gdf_cht_init = gdf_cht_init[cols_reqd]
        gdf_cht_init['cohort_id'] = pd.to_numeric(gdf_cht_init['cohort_id'], errors='coerce').fillna(0).astype(int)
        gdf_cht_init['polygon_id'] = pd.to_numeric(gdf_cht_init['polygon_id'], errors='coerce').fillna(0).astype(int)
        gdf_cht_init['cht2ply_id'] = pd.to_numeric(gdf_cht_init['cht2ply_id'], errors='coerce').fillna(0).astype(int)
        gdf_cht_init['op_id'] = pd.to_numeric(gdf_cht_init['op_id'], errors='coerce').fillna(0).astype(int)

        return gdf_cht_init[cols_reqd], cohort_gdf_init

    def merge_cohort_data_new(self, gdf_result, gdf_hist, cohort_gdf_init, cohort_ids, op_id):
        """
        Set the gdf.status_current = True/False and merge with gdf_cht_new
        """

        def merge_gdfs(gdf1, gdf2, cols):
            """
            Update NaN values in gdf1 (gdf_cht_combined) with values from gdf2 (cohort_gdf_init) based on cohort_id
            """
            # Create copies to avoid modifying originals
            gdf_result = gdf1.copy()
            gdf2_subset = gdf2[cols].copy()

            # Set cohort_id as index for both DataFrames
            gdf_result_indexed = gdf_result.set_index('cohort_id')
            gdf2_indexed = gdf2_subset.set_index('cohort_id')

            # Drop duplicate indexes, keep last
            gdf2_indexed = gdf2_indexed[~gdf2_indexed.index.duplicated(keep='last')]

            # Update only NaN values (overwrite=False means only replace NaN/None values)
            gdf_result_indexed.update(gdf2_indexed, overwrite=False)

            # Reset index and return
            return gdf_result_indexed.reset_index()

        if type(cohort_ids)!=list:
            cohort_ids = [cohort_ids]

        cols1 = ['polygon_id', 'poly_id_new', 'area_ha', 'cht_id_new']
        cols2 = ['polygon_id', 'poly_id_new', 'area_ha', 'cht_id_cur']

        # For assigning ASSIGN_CHT_TO_PLY - for the orig polygons assigned to ORIG cohort_id(s)
        gdf_cht_orig_Y = gdf_result[(gdf_result.poly_type=='CUT') & (gdf_result.cht_type=='ORIG')][cols1]
        gdf_cht_orig_Y['status_current'] = True
        gdf_cht_orig_Y['desc'] = 'ORIG-CUT_Y'
        gdf_cht_orig_Y = gdf_cht_orig_Y.rename(columns={'cht_id_new': 'cohort_id'})

        # For assigning ASSIGN_CHT_TO_PLY - for the new polygons assigned to NEW cohort_id(s)
        gdf_cht_new_Y = gdf_result[(gdf_result.poly_type=='BASE') & (gdf_result.cht_type=='NEW')][cols1]
        gdf_cht_new_Y['status_current'] = True
        gdf_cht_new_Y['desc'] = 'NEW-BASE_Y'
        gdf_cht_new_Y = gdf_cht_new_Y.rename(columns={'cht_id_new': 'cohort_id'})

        # For assigning ASSIGN_CHT_TO_PLY - for the new polygon id's assigned to OLD cohort_id(s)
        gdf_cht_new_N = gdf_result[(gdf_result.poly_type=='BASE') & (gdf_result.cht_type=='NEW')][cols2]
        gdf_cht_new_N['status_current'] = False
        gdf_cht_new_N['desc'] = 'NEW-BASE_N'
        gdf_cht_new_N = gdf_cht_new_N.rename(columns={'cht_id_cur': 'cohort_id'})

        # For assigning ASSIGN_CHT_TO_PLY - for the new polygon id's assigned to OLD cohort_id(s), that are new 'CUT' (not 'BASE')
        gdf_cht_new_Y_newcut = gdf_result[(gdf_result.poly_type=='CUT') & (gdf_result.cht_type=='NEW')][cols2]
        gdf_cht_new_Y_newcut['status_current'] = True
        gdf_cht_new_Y_newcut['desc'] = 'NEW-CUT_Y'
        gdf_cht_new_Y_newcut = gdf_cht_new_Y_newcut.rename(columns={'cht_id_cur': 'cohort_id'})

        gdf_cht_combined = pd.concat(
            [gdf_cht_orig_Y, gdf_cht_new_Y, gdf_cht_new_N, gdf_cht_new_Y_newcut],
            ignore_index=True,
            sort=False
        )

        # update with data from cohort_get_init
        gdf_cht_combined = merge_gdfs(
            gdf_cht_combined,
            cohort_gdf_init,
            ['cohort_id']
        )

        return gdf_cht_combined

    def assemble_gdf_result(self, gdf_result, gdf_hist, cohort_id, op_id, iter_seq, revision=None):
        '''
            Assembles the final result with polygon and cohort data
        '''

        # OPTIMIZED: Bulk spatial join instead of row-by-row apply()
        centroids_gdf = gpd.GeoDataFrame(
            geometry=gdf_result.geometry.representative_point().copy(),
            crs=gdf_result.crs
        )
        centroids_gdf['idx'] = range(len(centroids_gdf))

        gdf_hist_join = gdf_hist.copy()
        if 'index_right' in gdf_hist_join.columns:
            gdf_hist_join.drop('index_right', axis=1, inplace=True)

        joined = gpd.sjoin(centroids_gdf, gdf_hist_join, how="left", predicate="intersects")

        joined_reset = joined.reset_index(drop=True)
        gdf_result = gdf_result.reset_index(drop=True)
        gdf_result['polygon_id'] = joined_reset['polygon_id'].values
        gdf_result['name'] = joined_reset['name'].values
        gdf_result['compartment'] = joined_reset['compartment'].values
        gdf_result['sp_code'] = joined_reset['sp_code'].values
        gdf_result['polygon_id'] = gdf_result['polygon_id'].fillna(0).astype(int)
        gdf_result['area_ha'] = gdf_result.area/10000
        gdf_result['proposal_id'] = self.proposal_id
        gdf_result.drop(
            columns=['index','is_sliver','sliver_ratio', 'area', 'length','intersect_area', 'overlap_perc'],
            inplace=True, errors='ignore'
        )
        gdf_result = find_and_merge(gdf_result, self.threshold) # merge 'small' polygons with longest neighbour

        gdf_result = self.add_cht_id_to_gdf_sql(gdf_result)
        gdf_result = self.classify_polygons(gdf_result, self.gdf_single, tolerance=0.95)  # set poly_type 'CUT' or 'BASE'

        if 'index_right' in gdf_result.columns:
            gdf_result.drop('index_right', axis=1, inplace=True)

        gdf_result = gdf_result.explode()
        gdf_result.reset_index(inplace=True)

        # Write polygons to DB with revision
        operations_summary, gdf_result = write_polygons_to_db(
            gdf_result, self.request_metrics, iter_seq, revision
        )

        logger.info(f'\nCohort_id:  {cohort_id}')

        # Add new column cht_id_new
        gdf_result['cht_id_new'] = gdf_result['cht_id_cur'] # initialize column
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'cht_id_new'] = cohort_id # assign to new cohort

        # assign cohort id to new value for the additional duplicated/multiple polygon 'CUT's
        gdf_result.loc[
            (gdf_result['poly_type']=='CUT') & (gdf_result['polygon_id']!=gdf_result['poly_id_new']),
            'cht_id_new'
        ] = cohort_id

        # Add area_ha_orig column (from gdf_hist)
        gdf_result = gdf_result.merge(
            gdf_hist[['polygon_id', 'area_ha']].rename(columns={'area_ha': 'area_ha_orig', 'polygon_id': 'poly_id_new'}),
            on='poly_id_new',
            how='left',
        )

        # Add new column cht_type
        gdf_result['cht_type'] = 'NEW' # initialize column
        gdf_result.loc[gdf_result['cht_id_cur']==gdf_result['cht_id_new'], 'cht_type'] = 'ORIG' # assign to new cohort

        return gdf_result
