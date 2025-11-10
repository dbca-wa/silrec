from django.conf import settings
from django.db import models
from sqlalchemy import create_engine, text
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.ops import unary_union, polygonize

import json
import os
from confy import database

from silrec.utils.plot_utils import plot_gdf as plot
from silrec.utils.plot_utils import plot_overlay, plot_multi
from silrec.utils.plot_canvas import create_tabbed_charts
from silrec.utils.sliver_merge import find_and_merge
from silrec.utils.sliver_test1 import identify_slivers

from silrec.utils.write_polygons_to_db import write_gdf_to_tmp_polygon
from silrec.utils.write_cohort_to_db import create_cohort_record
#from silrec.utils.create_temp_tables import create_temp_tables_django_models, clear_temp_tables_django

#from silrec.components.proposals.models import PolygonHistory

import matplotlib as mpl
mpl.use('TkAgg')
#matplotlib.use('GTKAgg')
#matplotlib.use('Agg')

import logging
logger = logging.getLogger(__name__)



class ShapefileSliversMerger():
    '''
    04-Nov-2025
    Query postgres for intersected historical polygons for a single base_polygon at a time, and
    build the 'Poly - AssignPolygonToCohort - Cohort' tabulated data structure
    -------------------------------------------------------------------------------------------

    import geopandas as gpd
    from silrec.utils.shapefile_silvers_merger5 import ShapefileSliversMerger

    gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
    gdf_shp.to_crs('EPSG:28350', inplace=True)
    ssm = ShapefileSliversMerger(gdf_shp, proposal_id=1)
    gdf_merge_store = ssm.create_gdf()

    # Final Result in ssm.gdf_merge_store
    plot_gdf(ssm.gdf_merge_store[(ssm.gdf_merge_store.state=='GDF_RESULT_FILTERED') & (ssm.gdf_merge_store.iter_seq==16)])

    ssm.plot_canvas()

    plot_gdf(ssm.gdf_result_filtered)

    plot_gdf(find_and_merge(ssm.gdf_result_filtered, 20))

    plot_multi([self.gdf_shpfile, gdf_single, self.gdf_polygons_partitioned.explode(), gdf_slivers, gdf_result])
    ssm.plot_hist_polygons
    ssm.plot_hist_polygons_new
    ssm.plot_overlay
    ssm.plot_slivers
    ssm.plot_slivers_plus_base
    ssm.plot_slivers_merged
    ssm.plot_result


    1. Create multi_gdf - read multiple polygon topology
    -- 2. create multi_polygons gdf (hist intersecting) that intersect all (multiple polygon topology)
    3. iterate through each (base) polygon in multi_gdf - for each gdf_single
       a. for each loop --> ssm = ShapefileSliversMerger(gdf_single)
       b.                   create polygons gdf (hist intersecting) - need to check post sliver-merged 'data struc' if hist polygon(s) intersecting have split replacement (in DRAFT)
                            create a new polygons gdf eliminating hist polygons from silrec_v3 that have been replace by a previous loop split
       b.                   store 'processed_to_json_obj()' json data structure
       c.                   additionaly,
       c.                   reapeat loop (next base polygon)

    ---------
    21Oct2025

    import geopandas as gpd
    from silrec.utils.shapefile_silvers_merger3 import ShapefileSliversMerger

    gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
    gdf_shp.to_crs('EPSG:28350', inplace=True)
    ssm = ShapefileSliversMerger(gdf_shp, proposal_id=1)
    gdf_merge_store = ssm.create_gdf()

    gdf_result = ssm.gdf_merge_store[(ssm.gdf_merge_store.state=='GDF_RESULT_FILTERED') & (ssm.gdf_merge_store.iter_seq==16)]
    gdf_result.to_file('/home/jawaidm/projects/silrec/silrec/utils/Shapefiles/gdf_final_result/gdf_final_result.shp', driver='ESRI Shapefile')

    gdf_iter_results = ssm.gdf_merge_store[(ssm.gdf_merge_store.state=='GDF_RESULT_FILTERED')]
    gdf_iter_results.to_file('/home/jawaidm/projects/silrec/silrec/utils/Shapefiles/gdf_iter_results/gdf_iter_results.shp', driver='ESRI Shapefile')

    ---------
    04Nov2025

    import geopandas as gpd
    from silrec.utils.plot_utils import plot_gdf, plot_multi, plot_overlay
    from silrec.utils.shapefile_silvers_merger4 import ShapefileSliversMerger
    import json

    #gdf_shp.iloc[[0]].to_file('/home/ubuntu/projects/silrec/silrec/utils/Shapefiles/poly_Ap2c_cohort/gdf_0/gdf_0.shp', driver='ESRI Shapefile')

    gdf_shp_0 = gpd.read_file('silrec/utils/Shapefiles/poly_Ap2c_cohort/gdf_0/gdf_0.shp')
    gdf_shp_0.to_crs('EPSG:28350', inplace=True)
    ssm = ShapefileSliversMerger(gdf_shp_0, proposal_id=1)
    gdf_merge_store = ssm.create_gdf()

    gdf_result_filtered = ssm.gdf_merge_store[(ssm.gdf_merge_store.state=='GDF_RESULT_FILTERED') & (ssm.gdf_merge_store.iter_seq==1)]

    '''
    def __init__(self, gdf_shpfile, proposal_id, threshold=None, sql_polygons=None):
        self.gdf_shpfile = gdf_shpfile
        self.proposal_id = proposal_id
        self.threshold = threshold
        self.conn_engine = self.get_conn_engine()
        #self.gdf_hist_polygons_total = self.get_polygons_gdf(gdf_shpfile, 'tmp_polygon', sql_polygons)

        # for plots
#        self.gdf_polygons_intersecting_single = None
#        self.gdf_overlay = None
#        self.gdf_slivers = None
#        self.gdf_slivers_plus_base = None
#        self.gdf_slivers_merged = None
#        self.gdf_new_hist_polygons = None
#        self.gdf_result = None

    def get_conn_engine(self):
        '''
        an alternative solution for a multi-client (multi-tenant) application is to configure a different db user
        for each client, and configure the relevant search_path for each user:

        alter role user1 set search_path = "$user", public

        'postgresql://dev:dev123@localhost:5432/silrec_dev1',
        '''
        dbschema='silrec,public' # Searches left-to-right
        engine = create_engine(
            database.env('DATABASE_URL').replace('postgis','postgresql'),
            connect_args={'options': '-c search_path={}'.format(dbschema)}
        )
        return engine

#    @property
#    def next_iter_seq(self):
#        iter_seq = PolygonHistory.objects.filter(proposal_id=self.proposal_id).aggregate(models.Max('iter_seq'))['iter_seq__max']
#        return iter_seq + 1 if iter_seq is not None else 0
#
#    def save_global_intersecting_polygons(self, gdf, table_name='silrec_polygonhistory'):
#        ''' Save all polygons from forest_blocks.polygon (to PolygonHistory) that intersect the global (input) shapefile '''
#        gdf.to_postgis(table_name, con=self.conn_engine, if_exists='append', schema='silrec')

    def get_polygons_gdf(self, gdf, table_name, sql=None):
        ''' Get intersecting polygons from forest_blocks.polygon - intersecting with the given base polygon

            Returns --> SQL query result as gdf
        '''

        #import ipdb; ipdb.set_trace()
        if not sql:
            srid = 'SRID=' + settings.CRS_GDA94.split(':')[1] + '; ' # SRID=28350;
            #base_polygon_wkt = srid + gdf.dissolve().iloc[0].geometry.wkt
            #base_polygon_wkt = srid + gdf.iloc[0].geometry.wkt
            combined_geometry = unary_union(gdf['geometry'])
            base_polygon_wkt = srid + combined_geometry.wkt
            min_area_tolerance = 10

            #sql = f'''SELECT ph.polygon_id, ph.name, ph.geom FROM {table_name} AS ph WHERE ph.closed IS NULL AND ST_Intersects(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'));'''

#            sql = f'''SELECT ph.polygon_id, ph.name, ph.area_ha, ph.compartment, ph.sp_code, ph.geom
#                FROM {table_name} AS ph
#                WHERE ph.closed IS NULL
#                AND (
#                    ST_Overlaps(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
#                    OR ST_Contains(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
#                    OR ST_Within(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
#                    OR ST_Crosses(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
#                    AND ST_Area(ST_Intersection(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))) > {min_area_tolerance}
#                );'''

            sql = f'''SELECT
                    ph.polygon_id,
                    ph.name,
                    ph.area_ha,
                    ph.compartment,
                    ph.sp_code,
                    ph.geom,
                    ST_Area(ST_Intersection(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))) AS intersect_area,
                    (ST_Area(ST_Intersection(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))) / ph.area_ha) * 100 AS overlap_perc
                FROM {table_name} AS ph
                WHERE ph.closed IS NULL
                AND (
                    ST_Overlaps(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                    OR ST_Contains(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                    OR ST_Within(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                    OR ST_Crosses(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))
                )
                AND ST_Area(ST_Intersection(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'))) > {min_area_tolerance};'''


        gdf = gpd.read_postgis(sql, con=self.conn_engine, geom_col='geom')
        #import ipdb; ipdb.set_trace()

        gdf['poly_type'] = 'HIST'
        gdf['iter_seq'] = 1 #0 #self.next_iter_seq
        gdf['proposal_id'] = self.proposal_id
        gdf.rename(columns={'geom': 'geometry'}, inplace=True)
        gdf.set_geometry('geometry', inplace=True)
        gdf.set_crs(settings.CRS_GDA94)

        return gdf

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

        return gdf

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

    def init_gdf_merge_store(self, gdf_hist):
        gdf = gdf_hist.copy()
        #gdf['iter_seq'] = 0 #self.next_iter_seq
        gdf['iter_seq'] = 1
        gdf.rename(columns={'geom': 'geometry'}, inplace=True)
        gdf.set_geometry('geometry', inplace=True)
        gdf.set_crs(settings.CRS_GDA94)
        #import ipdb; ipdb.set_trace()
        return gdf

#        cohort_id = create_cohort_record(
#            engine=self.conn_engine,
#            obj_code=obje_code,
#            op_id=op_id,
#            year=year
#        )
#        return cohort_id

    def create_gdf(self):
        '''
        from silrec.utils.plot_utils import create_dummy_polygons, plot_gdf, plot_overlay, create_gdf
        polygons, gdf_single, gdf_polygons_intersecting_single, gdf_overlay, gdf_split, gdf_common_boundary, gdf_slivers, base_polygon, gdf_slivers_plus_base, gdf_new_hist_polygons, gdf_slivers_merged, gdf_result

        %matplotlib
        plot_gdf(gdf_slivers_merged)
        plot_gdf(gdf_new_hist_polygons)
        '''

        idx_count = 0
        gdf_shpfile = self.gdf_shpfile.copy()
        cohort_id = create_cohort_record(engine=self.conn_engine, obj_code='THIN', op_id=1, year=2024)

        #for index, row in self.gdf_shpfile.iloc[::-1].iterrows():
        for index, row in self.gdf_shpfile.iterrows():
            idx_count += 1
#            if idx_count==13:
#                import ipdb; ipdb.set_trace()

            self.gdf_single = gpd.GeoDataFrame([row], geometry=[row.geometry], crs=settings.CRS_GDA94)
            self.gdf_single  = self.set_data(self.gdf_single, iter_seq=idx_count, poly_type='BASE')

            import ipdb; ipdb.set_trace()
            gdf_hist = self.get_polygons_gdf(self.gdf_single, 'tmp_polygon')
            #import ipdb; ipdb.set_trace()

            # ---- TEMP
            gdf_hist.rename(columns={'geom': 'geometry'}, inplace=True)
            gdf_hist.set_geometry('geometry', inplace=True)
            gdf_hist.set_crs(settings.CRS_GDA94, inplace=True)
            #return self.gdf_single, gdf_hist
            # ----

            #self.gdf_single = gpd.read_file('silrec/utils/Shapefiles/demarcation_1_polygons/Demarcation_Boundary_1_polygons.shp')

            # Determine which geometries in polygons geodataframe (hist) intersect with any geometry in gdf_single
            # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
            intersects_mask_single = gdf_hist.geometry.intersects(self.gdf_shpfile.unary_union)
            gdf_polygons_intersecting_single = gdf_hist[intersects_mask_single]

            # non overlapping overlayed geometries (creates independent partitioned geometries)
            self.gdf_polygons_partitioned = gpd.overlay(self.gdf_single[['geometry']], gdf_polygons_intersecting_single, how='union')
            self.gdf_polygons_partitioned = self.gdf_polygons_partitioned[self.gdf_polygons_partitioned.area>1] # drop tiny areas
            self.gdf_polygons_partitioned = self.gdf_polygons_partitioned.explode() # explode multipolys to indep polys
            self.gdf_polygons_partitioned.reset_index(inplace=True)
            #import ipdb; ipdb.set_trace()

            #import ipdb; ipdb.set_trace()
            base_polygon = self.get_base_polygon_gdf(self.gdf_single, self.gdf_polygons_partitioned)[['geometry']]
            base_polygon['iter_seq'] = idx_count
            base_polygon['poly_type'] = 'BASE'

            # extract the land slivers
            self.threshold = self.threshold if self.threshold else settings.SLIVER_AREALENGTH_THRESHOLD
            #import ipdb; ipdb.set_trace()
            gdf_slivers = identify_slivers(self.gdf_polygons_partitioned.explode(), base_polygon, sliver_threshold=self.threshold) # better since returns all slivers touching base_polygon
            gdf_slivers['poly_type'] = 'SLVR'
            mask = self.gdf_polygons_partitioned.explode().geometry.area/self.gdf_polygons_partitioned.explode().geometry.length < self.threshold
            gdf_excl_slivers = self.gdf_polygons_partitioned.explode()[~(mask)]
            gdf_slivers_plus_base = gpd.GeoDataFrame(pd.concat([gdf_slivers, base_polygon], ignore_index=True))

            # re-merge land slivers to base_polygon and create poly_type column
            gdf_excl_slivers_plus_base = gpd.overlay(self.gdf_polygons_partitioned, gdf_slivers_plus_base, how='difference')
            gdf_excl_slivers_plus_base['poly_type'] = 'HIST'
            gdf_slivers_merged = gdf_slivers_plus_base.dissolve()
            gdf_slivers_merged['poly_type'] = 'BASE'
            gdf_slivers_merged['polygon_id'] = 0
            gdf_slivers_merged['proposal_id'] = self.proposal_id

            #import ipdb; ipdb.set_trace()
            # re-merge merged base_polygon with remaining cookie-cut and hist polygons
            gdf_result = gpd.GeoDataFrame(pd.concat([gdf_excl_slivers_plus_base, gdf_slivers_merged], ignore_index=True))
            gdf_result = gdf_result[gdf_result.area>1] # drop tiny areas
            gdf_result['iter_seq'] = idx_count
            gdf_result = self.assemble_gdf_result(gdf_result, gdf_hist, cohort_id)

            # get init 'polygon - assign_cht_to_ply - cohort' state
            gdf_cht_init = self.merge_cohort_data_with_sqlalchemy(gdf_result, self.conn_engine)


            # add column identifying store type
            gdf_hist['state']        = "gdf_hist".upper()
            self.gdf_single['state'] = "gdf_single".upper()
            gdf_result['state']      = "gdf_result".upper()
            gdf_cht_init['state']      = "gdf_cht_init".upper()


            import ipdb; ipdb.set_trace()
            list_state = [
                gdf_hist.copy(),
                self.gdf_single.copy(),
                gdf_result.copy(),
                gdf_cht_init.copy(),
            ]

            #import ipdb; ipdb.set_trace()
            print(gdf_hist)
            print()
            print(gdf_result)
            print()
            gdf_store = self.store_state(list_state)
            print(gdf_store)
            import ipdb; ipdb.set_trace()
            gdf_hist = gdf_result.copy()
            gdf_hist['iter_seq'] = gdf_hist.iter_seq + 1

            pass

        return gdf_store

    def set_data(self, gdf, iter_seq=None, polygon_id=0, poly_type=None):
        gdf['proposal_id'] = self.proposal_id
        gdf['iter_seq'] = iter_seq
        gdf['polygon_id'] = polygon_id if 'polygon_id' not in gdf else gdf['polygon_id'].fillna(polygon_id)
#        if 'poly_type' not in gdf or gdf['poly_type'].isna().any():
        if poly_type == 'SLVR':
            try:
                gdf['poly_type'] = gdf['poly_type'].fillna('SLVR')
            except:
                gdf['poly_type'] = 'SLVR'

        elif poly_type == 'BASE':
            gdf['poly_type'] = 'HIST'
#            try:
#                gdf['poly_type'] = gdf['poly_type'].fillna('HIST')
#            except:
#                gdf['poly_type'] = 'HIST'

            base_polygon = self.get_base_polygon_gdf(self.gdf_single, self.gdf_shpfile)
            if not base_polygon.empty:
                print('2')
                #import ipdb; ipdb.set_trace()
                gdf.at[base_polygon.iloc[0].name, 'poly_type'] = 'BASE' # 'BASE'

        else:
            logger.error(f'poly_type {poly_type} not recognised')

        return gdf

    def store_state(self, gdf_list):
        fields = [
            'name',
            'polygon_id',
            'poly_id_new',
            'poly_type',
            'cht_type',
            'cht_id_cur',
            'cht_id_new',
            'area_ha_orig',
            'area_ha',
            'state',
            'op_id',
            'complete_date',
            'obj_code',
            'fea_id',
            'target_ba_',
            'compartment',
            'sp_code',
            'iter_seq',
            'proposal_id',
            'Region',
            'Block',
            'Block_cpt',
            'Compno',
            'Ops_status',
            'Veg_comple',
            'Lmu',
            'herbicide_',
            'Zone',
            'compartmen',
            'vrp_id',
            'geometry',
        ]

#        gdf_store = gpd.GeoDataFrame()
#        for gdf in gdf_list:
#            gdf_store = pd.concat([
#                                gdf_store,
#                                gdf],
#                                axis=0,
#                                ignore_index=True
#                            )
#            #gdf[['polygon_id','poly_type','iter_seq','proposal_id', 'state', 'geometry']]],

        gdf_store = pd.concat(gdf_list, ignore_index=True)
        return gdf_store[fields]

    @property
    def gdf_result_filtered(self):
        iters = [int(item) for item in self.gdf_merge_store.iter_seq.unique() if not (isinstance(item, float) and np.isnan(item))]
        return self.gdf_merge_store[(self.gdf_merge_store.state=='GDF_RESULT_FILTERED') & (self.gdf_merge_store.iter_seq==max(iters))]

    def plot_canvas(self):
        '''
        import geopandas as gpd
        from silrec.utils.shapefile_silvers_merger3 import ShapefileSliversMerger

        gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
        gdf_shp.to_crs('EPSG:28350', inplace=True)
        ssm = ShapefileSliversMerger(gdf_shp, proposal_id=1)

        gdf_merge_store = ssm.create_gdf()
        ssm.plot_canvas()

        '''
        iters = [int(item) for item in self.gdf_merge_store.iter_seq.unique() if not (isinstance(item, float) and np.isnan(item))]
        iters.insert(0, 0)
        states = [item for item in self.gdf_merge_store.state.unique() if not (isinstance(item, float) and np.isnan(item))]

        gdf_iter_list = []
        chart_titles_list = []
        for it in iters[:3]:
        #for it in iters:
            gdf_state_list = []
            chart_titles = []
            #import ipdb; ipdb.set_trace()
            if it == 0:
                # Plot Summary on first Tab
                gdf_state_list.append(self.gdf_shpfile)
                gdf_state_list.append(self.gdf_hist_polygons_total)

                #gdf_result_filtered = self.gdf_merge_store[(self.gdf_merge_store.state=='GDF_RESULT_FILTERED') & (self.gdf_merge_store.iter_seq==max(iters))]
                gdf_state_list.append(self.gdf_result_filtered)
                chart_titles.append(f'Shpfile: Polys {len(self.gdf_shpfile)}, Area_HA {round(self.gdf_shpfile.area.sum()/10000, 2)}')
                chart_titles.append(f'Hist: Polys {len(self.gdf_hist_polygons_total)}, Area_HA {round(self.gdf_hist_polygons_total.area.sum()/10000, 2)}')
                chart_titles.append(f'Result: Polys {len(self.gdf_result_filtered)}, Area_HA {round(self.gdf_result_filtered.area.sum()/10000, 2)}')

            else:
                for state in states:
                    #self.gdf_merge_store[(self.gdf_merge_store.state=='GDF_RESULT_FILTERED') & (self.gdf_merge_store.iter_seq==16)]
                    gdf = self.gdf_merge_store[(self.gdf_merge_store.state==state) & (self.gdf_merge_store.iter_seq==it)]
                    gdf['colour'] = gdf['poly_type'].apply(lambda x: 'grey' if x=='BASE' else ('green' if x=='CUT' else ('yellow' if x=='SLVR' else 'BLUE')))
                    gdf_state_list.append(gdf)
                    chart_titles.append(f'{state} - Polygons {len(gdf)}, Area_HA {round(gdf.area.sum()/10000, 2)}')

            gdf_iter_list.append(gdf_state_list)
            chart_titles_list.append(chart_titles)

        #create_tabbed_charts(*gdf_iter_list, chart_titles=[states,states,states])
        create_tabbed_charts(*gdf_iter_list, chart_titles=chart_titles_list)

    def classify_polygons(self, gdf_result, gdf_single, tolerance=0.95):
        """
        Classify polygons in gdf_result based on their spatial relationship with gdf_single
        with area-based tolerance.

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
                print(f"Error processing geometry: {e}")
                poly_types.append('CUT')

        gdf_result['poly_type'] = poly_types
        gdf_result['area_ratio'] = [intersection.area / geom.area if geom and not geom.is_empty else 0.0
                                for geom, intersection in zip(gdf_result.geometry,
                                                            [g.intersection(hist_union) for g in gdf_result.geometry])]
        return gdf_result

    def add_cht_id_with_django_orm(self, gdf_result):
        ''' Django ORM approach
        '''
        # Get polygon_ids
        polygon_ids = gdf_result['polygon_id'].tolist()

        # Query using Django ORM
        queryset = TmpAssignChtToPly.objects.filter(
            polygon_id__in=polygon_ids,
            status_current=True
        ).values('polygon_id', 'cohort_id')

        # Create mapping dictionary
        cohort_mapping = {item['polygon_id']: item['cohort_id'] for item in queryset}

        # Apply to GeoDataFrame using apply
        gdf_result['cht_id_cur'] = gdf_result.apply(
            lambda row: cohort_mapping.get(row['polygon_id']),
            axis=1
        )

        return gdf_result

    def add_cht_id_with_sqlalchemy(self, gdf_result, engine):
        ''' SQLAlchemy approach
        '''

        polygon_ids = gdf_result['polygon_id'].tolist()

        # Using text() for safe parameterized queries
        query = text("""
            SELECT polygon_id, cohort_id
            FROM tmp_assign_cht_to_ply
            WHERE polygon_id = ANY(:polygon_ids) AND status_current = true
        """)

        with engine.connect() as conn:
            result = conn.execute(query, {'polygon_ids': polygon_ids})
            cohort_mapping = {row[0]: row[1] for row in result}

        # Apply using map (more efficient than apply for simple mapping)
        gdf_result['cht_id_cur'] = gdf_result['polygon_id'].map(cohort_mapping)

        return gdf_result

    def merge_cohort_data_with_sqlalchemy(self, gdf_result, engine):
        """
        Query PostgreSQL for cohort data and merge with GeoDataFrame
        Uses parameterized query for security

        import geopandas as gpd
        from silrec.utils.plot_utils import plot_gdf, plot_multi, plot_overlay
        from silrec.utils.shapefile_silvers_merger4 import ShapefileSliversMerger
        import json
        from silrec.utils.create_temp_tables import create_temp_tables_django_models, clear_temp_tables_django

        clear_temp_tables_django()
        create_temp_tables_django_models()

        gdf_shp_0 = gpd.read_file('silrec/utils/Shapefiles/poly_Ap2c_cohort/gdf_0/gdf_0.shp')
        gdf_shp_0.to_crs('EPSG:28350', inplace=True)
        ssm = ShapefileSliversMerger(gdf_shp_0, proposal_id=1)
        gdf_store = ssm.create_gdf(True)

        cols = ['polygon_id', 'area_ha_orig', 'poly_type', 'cht_type', 'cht_id_cur', 'obj_code', 'iter_seq', 'proposal_id']
        cols2 = cols + ['op_id', 'complete_date', 'target_ba_m2ha']

        gdf_cht_init[cols2]
        OR
        gdf_store[(gdf_store.state=='GDF_CHT_INIT') & (gdf_store.iter_seq==1)][cols2]
        """

        cols = ['polygon_id', 'area_ha_orig', 'poly_type', 'cht_type', 'cht_id_cur',
                'obj_code', 'iter_seq', 'proposal_id']
        cols2 = cols + ['op_id', 'complete_date', 'target_ba_m2ha']

        gdf_cht_init = gdf_result[gdf_result.polygon_id==gdf_result.poly_id_new][cols].copy()

        if gdf_cht_init.empty:
            return gdf_result

        # Build parameterized query
#        query = text("""
#            SELECT cohort_id, obj_code, complete_date, target_ba_m2ha
#            FROM tmp_cohort
#            WHERE cohort_id = ANY(:cohort_ids)
#        """)

        query = text("""
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
            FROM tmp_polygon tp
            LEFT JOIN tmp_assign_cht_to_ply tactp ON tp.polygon_id = tactp.polygon_id
            LEFT JOIN tmp_cohort tc ON tactp.cohort_id = tc.cohort_id
            WHERE tc.cohort_id = ANY(:cohort_ids) AND tactp.status_current='True';
        """)

        with engine.connect() as conn:
            cohort_df = pd.read_sql(query, conn, params={'cohort_ids': gdf_cht_init.cht_id_cur.to_list()})

        # Merge with original GeoDataFrame
        gdf_cht_init = gdf_cht_init.merge(
            cohort_df,
            left_on='cht_id_cur',
            right_on='cohort_id',
            how='left'
        )
        import ipdb; ipdb.set_trace()

        if 'obj_code' not in gdf_cht_init.columns:
            gdf_cht_init = gdf_cht_init.drop('obj_code_x', axis=1)
            gdf_cht_init = gdf_cht_init.rename(columns={'obj_code_y': 'obj_code'})
        if 'polygon_id' not in gdf_cht_init.columns:
            gdf_cht_init = gdf_cht_init.drop('polygon_id_x', axis=1)
            gdf_cht_init = gdf_cht_init.rename(columns={'polygon_id_y': 'polygon_id'})

        # Strip blank spaces from obj_code
        gdf_cht_init['obj_code'] = gdf_cht_init['obj_code'].str.strip()

        return gdf_cht_init

    def assemble_gdf_result(self, gdf_result, gdf_hist, cohort_id):
        '''
            # gdf_result[['polygon_id', 'poly_id_new','name', 'area_ha_orig', 'area_ha', 'compartment', 'poly_type','cht_type', 'cht_id_cur', 'cht_id_new', 'fea_id', 'obj_code', 'target_ba_']]

            1. Where the cht_type=='ORIG',
                 a. No changes necessary to assign_cht_to_ply table records, since Area already updated in Polygon table
            2. Where the cht_type=='NEW',
                 b. update/set original cohort_id's cohort.status_current to False
                 c. add new records to assign_cht_to_ply table --> link ''poly_id_new' to ''cht_id_new' (cohort.status_current=True)
        '''


        def get_base_polygon_field(row, col_name, gdf_hist):
            ''' for given split polygon, returns the polygon_id of the parent (historical polygons gdf) polygon
                usage: gdf_tmp['polygon_id'] = gdf_tmp.apply(get_base_polygon_field, axis=1, args=('col_name',))
                --> Returns the parent polygon_id (intersected by the centroid - representative_point() falls inside the polygon)
            '''
            # Convert Centroid POINT to GDF
            #import ipdb; ipdb.set_trace()
            centroid_point = row.geometry.representative_point()
            data = {'geometry': [centroid_point]}
            centroid_gdf = gpd.GeoDataFrame(data, geometry='geometry', crs=settings.CRS_GDA94)

            #if 'index_right' in self.gdf_hist_polygons_total.columns:
            if 'index_right' in gdf_hist.columns:
                self.polygons.drop(['index_right'], axis=1, inplace=True)

            #gdf = gpd.sjoin(self.gdf_hist_polygons_total, centroid_gdf, how="inner", predicate="intersects")
            gdf = gpd.sjoin(gdf_hist, centroid_gdf, how="inner", predicate="intersects")
            return None if gdf.empty else gdf[col_name].iloc[0]

        # identify and assign the src polygon from active hist polygon (silrec_v3)
        gdf_result['polygon_id'] = gdf_result.apply(get_base_polygon_field, axis=1, args=('polygon_id', gdf_hist)) # add column for the corresponding hist polygon_id
        gdf_result['name'] = gdf_result.apply(get_base_polygon_field, axis=1, args=('name', gdf_hist)) # add column for the corresponding hist polygon_id
        gdf_result['compartment'] = gdf_result.apply(get_base_polygon_field, axis=1, args=('compartment', gdf_hist)) # add column for the corresponding hist polygon_id
        gdf_result['sp_code'] = gdf_result.apply(get_base_polygon_field, axis=1, args=('sp_code', gdf_hist)) # add column for the corresponding hist polygon_id
        gdf_result['polygon_id'] = gdf_result['polygon_id'].fillna(0).astype(int)
        gdf_result['area_ha'] = gdf_result.area/10000
        gdf_result['proposal_id'] = self.proposal_id
        gdf_result.drop(columns=['index','is_sliver','sliver_ratio', 'area', 'length','intersect_area', 'overlap_perc'], inplace=True)
        gdf_result = find_and_merge(gdf_result, self.threshold)
        self.add_cht_id_with_sqlalchemy(gdf_result, self.conn_engine)
        gdf_result = self.classify_polygons(gdf_result, self.gdf_single, tolerance=0.95)

        # add data from shapefile attributes
        gdf_result[['fea_id', 'obj_code', 'target_ba_']] = None # initialize column
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'fea_id']     = self.gdf_single.fea_id.iloc[0]
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'obj_code']   = self.gdf_single.obj_code.iloc[0]
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'target_ba_'] = self.gdf_single.target_ba_.iloc[0]

        if 'index_right' in gdf_result.columns:
            gdf_result.drop('index_right', axis=1, inplace=True)

        operations_summary, gdf_result = write_gdf_to_tmp_polygon(
            gdf_result=gdf_result,
            engine=self.conn_engine,
            current_user="system"
        )
        logger.info(f'\nCohort_id:  {cohort_id}')

        # Add new colum cht_id_cur
        gdf_result['cht_id_new'] = gdf_result['cht_id_cur'] # initialize column
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'cht_id_new'] = cohort_id # assign tp new cohort

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
        gdf_result.loc[gdf_result['cht_id_cur']==gdf_result['cht_id_new'], 'cht_type'] = 'ORIG' # assign tp new cohort

        return gdf_result

