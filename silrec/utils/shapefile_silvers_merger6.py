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
from django.utils import timezone
from confy import database

from silrec.utils.plot_utils import plot_gdf as plot
from silrec.utils.plot_utils import plot_overlay, plot_multi
from silrec.utils.plot_canvas import create_tabbed_charts
from silrec.utils.sliver_merge import find_and_merge
from silrec.utils.sliver_test1 import identify_slivers

from silrec.utils.write_polygons_to_db import write_gdf_to_tmp_polygon
from silrec.utils.write_cohort_to_db import create_cohort_record
#from silrec.utils.create_temp_tables import create_temp_tables_django_models, clear_temp_tables_django


import matplotlib as mpl
# mpl.use('TkAgg')
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


    ----------------------
    11-Nov-2025

    import geopandas as gpd
    from silrec.utils.plot_utils import plot_gdf, plot_multi, plot_overlay
    from silrec.utils.shapefile_silvers_merger5 import ShapefileSliversMerger
    import json
    from silrec.utils.create_temp_tables import create_temp_tables, drop_temp_tables_django

    drop_temp_tables_django()
    create_temp_tables()

    gdf_shp_0 = gpd.read_file('silrec/utils/Shapefiles/poly_Ap2c_cohort/gdf_0/gdf_0.shp')
    gdf_shp_0.to_crs('EPSG:28350', inplace=True)

    gdf_shp_16 = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
    gdf_shp_16.to_crs('EPSG:28350', inplace=True)

    ssm = ShapefileSliversMerger(gdf_shp_0, proposal_id=1)
    gdf_store = ssm.create_gdf()

    drop_temp_tables_django()
    create_temp_tables()
    ssm = ShapefileSliversMerger(gdf_shp_0, proposal_id=1)
    gdf_store = ssm.create_gdf()

    gdf_store.state

    gdf_hist   = gdf_store[(gdf_store.state=='GDF_HIST') & (gdf_store.iter_seq==1)]
    gdf_single = gdf_store[(gdf_store.state=='GDF_SINGLE') & (gdf_store.iter_seq==1)]
    gdf_result = gdf_store[(gdf_store.state=='GDF_RESULT') & (gdf_store.iter_seq==1)]

    plot_gdf(gdf_shp_0)
    plot_gdf(gdf_hist)
    plot_gdf(gdf_single)
    plot_gdf(gdf_result)

    plot_overlay(gdf_hist, gdf_single)
    plot_multi([gdf_hist, gdf_single, gdf_result])

    cols_init = ['polygon_id','cohort_id', 'cht2ply_id', 'name', 'area_ha_orig', 'obj_code', 'fea_id', 'complete_date', 'target_ba_m2ha', 'status_current']
    cols_new = ['polygon_id', 'cohort_id', 'area_ha', 'fea_id', 'obj_code', 'target_ba_', 'status_current', 'desc']

    gdf_store[(gdf_store.state=='GDF_CHT_INIT') & (gdf_store.iter_seq==1)][cols_init]
    gdf_store[(gdf_store.state=='GDF_CHT_NEW') & (gdf_store.iter_seq==1)][cols_new]

    plot_multi([gdf_hist, gdf_result, gdf_result], user_defined_label=['polygon_id', 'polygon_id', 'poly_id_new'])
    plot_multi([gdf_hist, gdf_result, gdf_result])
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

    @staticmethod
    def get_conn_engine():
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

    @staticmethod
    def get_polygons_gdf(gdf, table_name, conn_engine, proposal_id, sql=None):
        ''' Get intersecting polygons from forest_blocks.polygon - intersecting with the given base polygon

            Returns --> SQL query result as gdf
        '''

        if not sql:
            srid = 'SRID=' + settings.CRS_GDA94.split(':')[1] + '; ' # SRID=28350;
            combined_geometry = unary_union(gdf['geometry'])
            base_polygon_wkt = srid + combined_geometry.wkt
            min_area_tolerance = 10

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


        #gdf = gpd.read_postgis(sql, con=self.conn_engine, geom_col='geom')
        gdf = gpd.read_postgis(sql, con=conn_engine, geom_col='geom')

        gdf['poly_type'] = 'HIST'
        gdf['iter_seq'] = 1 #0 #self.next_iter_seq
        #gdf['proposal_id'] = self.proposal_id
        gdf['proposal_id'] = proposal_id
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
        cohort_id = create_cohort_record(engine=self.conn_engine, obj_code='JCROP1', op_id=1, year=2024)

        list_state = []
        #for index, row in self.gdf_shpfile.iloc[::-1].iterrows():
        for index, row in self.gdf_shpfile.iterrows():
            idx_count += 1
#            if idx_count==13:
#                import ipdb; ipdb.set_trace()

            #import ipdb; ipdb.set_trace()
            self.gdf_single = gpd.GeoDataFrame([row], geometry=[row.geometry], crs=settings.CRS_GDA94)
            self.gdf_single  = self.set_data(self.gdf_single, iter_seq=idx_count, poly_type='BASE')

            #import ipdb; ipdb.set_trace()
            gdf_hist = self.get_polygons_gdf(self.gdf_single, 'tmp_polygon', self.conn_engine, self.proposal_id)
            import ipdb; ipdb.set_trace()

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
            #import ipdb; ipdb.set_trace()
            gdf_cht_init, cohort_gdf_init = self.merge_cohort_data_init(gdf_result)
            gdf_cht_new = self.merge_cohort_data_new(gdf_result, gdf_hist, cohort_gdf_init, cohort_id)
            gdf_cht_init['iter_seq'] = idx_count
            gdf_cht_new['iter_seq'] = idx_count

            # add column identifying store type
            gdf_hist['state']        = "gdf_hist".upper()
            self.gdf_single['state'] = "gdf_single".upper()
            gdf_result['state']      = "gdf_result".upper()
            gdf_cht_init['state']    = "gdf_cht_init".upper()
            gdf_cht_new['state']     = "gdf_cht_new".upper()

            import ipdb; ipdb.set_trace()
            gdf_store = {
                "gdf_hist".upper(): gdf_hist.copy(),
                "gdf_single".upper(): self.gdf_single.copy(),
                "gdf_result".upper(): gdf_result.copy(),
                "gdf_cht_init".upper(): gdf_cht_init.copy(),
                "gdf_cht_new".upper(): gdf_cht_new.copy(),
            }

            list_state.append(
                gdf_store
            )
#            list_state.append([
#                gdf_hist.copy(),
#                self.gdf_single.copy(),
#                gdf_result.copy(),
#                gdf_cht_init.copy(),
#                gdf_cht_new.copy(),
#            ])

            #gdf_store = self.store_state(list_state)
            #import ipdb; ipdb.set_trace()
            self.save_cht_new_to_db(gdf_cht_new)
            gdf_hist = gdf_result.copy()
            gdf_hist['iter_seq'] = gdf_hist.iter_seq + 1

        #return gdf_store
        return list_state

    def set_data(self, gdf, iter_seq=None, polygon_id=0, poly_type=None):
        gdf['proposal_id'] = self.proposal_id
        gdf['iter_seq'] = iter_seq
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

    def store_state(self, gdf_list):
        gdf_store = pd.concat(gdf_list, ignore_index=True)
        gdf_store['polygon_id'] = gdf_store['polygon_id'].fillna(0).astype(int)
        gdf_store['cohort_id']  = gdf_store['cohort_id'].fillna(0).astype(int)
        gdf_store['cht2ply_id'] = gdf_store['cht2ply_id'].fillna(0).astype(int)
#        gdf_store['target_ba_'] = gdf_store['target_ba_'].fillna(-1).astype(int)
        return gdf_store

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
                print(f"Error processing geometry: {e}")
                poly_types.append('CUT')

        gdf_result['poly_type'] = poly_types
        gdf_result['area_ratio'] = [intersection.area / geom.area if geom and not geom.is_empty else 0.0
        for geom, intersection in zip(gdf_result.geometry,
            [g.intersection(hist_union) for g in gdf_result.geometry])]

        return gdf_result

    def add_cht_id_to_gdf_sql_orm(self, gdf_result):
        ''' Query the DB table tmp_assign_cht_to_ply for ply_id's, cht_id's
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

    def add_cht_id_to_gdf_sql(self, gdf_result):
        ''' Query the DB table tmp_assign_cht_to_ply for ply_id's, cht_id's
        '''

        polygon_ids = gdf_result['polygon_id'].tolist()

        # Using text() for safe parameterized queries
        query = text("""
            SELECT polygon_id, cohort_id
            FROM tmp_assign_cht_to_ply
            WHERE polygon_id = ANY(:polygon_ids) AND status_current = True
        """)

        with self.conn_engine.connect() as conn:
            result = conn.execute(query, {'polygon_ids': polygon_ids})
            cohort_mapping = {row[0]: row[1] for row in result}

        # Apply using map (more efficient than apply for simple mapping)
        gdf_result['cht_id_cur'] = gdf_result['polygon_id'].map(cohort_mapping)

        return gdf_result

    def merge_cohort_data_init(self, gdf_result):
        """
        Query DB for cohort data.
        Namely, from 'polygon - assign_cht_to_ply - cohort' triple using SQL JOIN and merge with gdf
        """

        cols = ['polygon_id', 'area_ha_orig', 'poly_type', 'cht_type', 'cht_id_cur', 'obj_code', 'iter_seq', 'proposal_id']
        gdf_cht_init = gdf_result[gdf_result.polygon_id==gdf_result.poly_id_new][cols].copy()

        if gdf_cht_init.empty:
            return gdf_result

        cohort_ids = gdf_result.cht_id_cur.to_list()
        cohort_ids = list(set(cohort_ids))
        if len(cohort_ids) == 0:
            return None

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
            WHERE tc.cohort_id = ANY(:cohort_ids) AND tactp.status_current=True;
        """)

        with self.conn_engine.connect() as conn:
            cohort_gdf_init = pd.read_sql(query, conn, params={'cohort_ids': cohort_ids})

        # Merge with original GeoDataFrame
        gdf_cht_init = gdf_cht_init.merge(
            cohort_gdf_init,
            left_on='cht_id_cur',
            right_on='cohort_id',
            how='left'
        )

        if 'obj_code' not in gdf_cht_init.columns:
            gdf_cht_init = gdf_cht_init.drop('obj_code_x', axis=1)
            gdf_cht_init = gdf_cht_init.rename(columns={'obj_code_y': 'obj_code'})

        if 'polygon_id' not in gdf_cht_init.columns:
            gdf_cht_init = gdf_cht_init.drop('polygon_id_x', axis=1)
            gdf_cht_init = gdf_cht_init.rename(columns={'polygon_id_y': 'polygon_id'})

        # Strip blank spaces from obj_code
        gdf_cht_init['obj_code'] = gdf_cht_init['obj_code'].str.strip()
        #gdf_cht_init = gdf_cht_init.rename(columns={'area_ha_orig': 'area_ha'})

        cols_reqd = ['cohort_id', 'polygon_id', 'cht2ply_id', 'name', 'area_ha_orig', 'obj_code', 'complete_date', 'target_ba_m2ha', 'status_current']
        #import ipdb; ipdb.set_trace()
        return gdf_cht_init[cols_reqd], cohort_gdf_init

    def merge_cohort_data_new(self, gdf_result, gdf_hist, cohort_gdf_init, cohort_ids):
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

            # Update only NaN values (overwrite=False means only replace NaN/None values)
            gdf_result_indexed.update(gdf2_indexed, overwrite=False)

            # Reset index and return
            return gdf_result_indexed.reset_index()

        def update_columns(row):
            if row['desc'] == 'NEW-BASE_N':
                # Find matching row with same polygon_id (could be any desc except NEW-BASE_N)
                matching_rows = gdf_cht_combined[
                    (gdf_cht_combined['polygon_id'] == row['polygon_id']) &
                    (gdf_cht_combined['desc'] != 'NEW-BASE_N')  # Exclude current type of row
                ]
                if not matching_rows.empty:
                    # Take the first matching row's values for all three columns
                    matching_row = matching_rows.iloc[0]
                    row['fea_id'] = matching_row['fea_id']
                    row['obj_code'] = matching_row['obj_code']
                    row['target_ba_'] = matching_row['target_ba_']
            return row

        if type(cohort_ids)!=list:
            cohort_ids = [cohort_ids]

        # select cohort_id, obj_code, complete_date, target_ba_m2ha from tmp_cohort where cohort_id=191351;
#        query = text("""
#            SELECT
#                cohort_id,
#                obj_code,
#                op_id,
#                complete_date,
#                target_ba_m2ha
#            FROM tmp_cohort
#            WHERE cohort_id = ANY(:cohort_ids);
#        """)
#
#        with self.conn_engine.connect() as conn:
#            cohort_df = pd.read_sql(query, conn, params={'cohort_ids': cohort_ids})

        cols1 = ['polygon_id', 'poly_id_new', 'area_ha', 'cht_id_new', 'fea_id', 'obj_code', 'target_ba_']
        cols2 = ['polygon_id', 'poly_id_new', 'area_ha', 'cht_id_cur', 'fea_id', 'obj_code', 'target_ba_']

        # For assigning ASSIGN_CHT_TO_PLY - for the orig polygons assigned to ORIG cohort_id(s) - These don't need saving since they should already be present
        # in the ASSIGN_CHT_TO_PLY table
        #gdf_cht_orig_Y = gdf_result[(gdf_result.poly_type=='CUT') & (gdf_result.cht_type=='ORIG')][['poly_id_new','area_ha','cht_id_new']]
        gdf_cht_orig_Y = gdf_result[(gdf_result.poly_type=='CUT') & (gdf_result.cht_type=='ORIG')][cols1]
        gdf_cht_orig_Y['status_current'] = True
        gdf_cht_orig_Y['desc'] = 'ORIG-CUT_Y'
        #gdf_cht_orig_Y = gdf_cht_orig_Y.rename(columns={'poly_id_new': 'polygon_id', 'cht_id_new': 'cohort_id'})
        gdf_cht_orig_Y = gdf_cht_orig_Y.rename(columns={'cht_id_new': 'cohort_id'})

        # For assigning ASSIGN_CHT_TO_PLY - for the new polygons assigned to NEW cohort_id(s)
        #gdf_cht_new_Y = gdf_result[(gdf_result.poly_type=='BASE') & (gdf_result.cht_type=='NEW')][['poly_id_new','area_ha','cht_id_new']]
        gdf_cht_new_Y = gdf_result[(gdf_result.poly_type=='BASE') & (gdf_result.cht_type=='NEW')][cols1]
        gdf_cht_new_Y['status_current'] = True
        gdf_cht_new_Y['desc'] = 'NEW-BASE_Y'
        #gdf_cht_new_Y = gdf_cht_new_Y.rename(columns={'poly_id_new': 'polygon_id', 'cht_id_new': 'cohort_id'})
        gdf_cht_new_Y = gdf_cht_new_Y.rename(columns={'cht_id_new': 'cohort_id'})

        # For assigning ASSIGN_CHT_TO_PLY - for the new polygon id's assigned to OLD cohort_id(s)
        #gdf_cht_new_N = gdf_result[(gdf_result.poly_type=='BASE') & (gdf_result.cht_type=='NEW')][['poly_id_new','area_ha','cht_id_cur']]
        gdf_cht_new_N = gdf_result[(gdf_result.poly_type=='BASE') & (gdf_result.cht_type=='NEW')][cols2]
        gdf_cht_new_N['status_current'] = False
        gdf_cht_new_N['desc'] = 'NEW-BASE_N'
        #gdf_cht_new_N = gdf_cht_new_N.rename(columns={'poly_id_new': 'polygon_id', 'cht_id_cur': 'cohort_id'})
        gdf_cht_new_N = gdf_cht_new_N.rename(columns={'cht_id_cur': 'cohort_id'})

        # For assigning ASSIGN_CHT_TO_PLY - for the new polygon id's assigned to OLD cohort_id(s), that are not 'CUT' (not 'BASE')
        #gdf_cht_new_Y_newcut = gdf_result[(gdf_result.poly_type=='CUT') & (gdf_result.cht_type=='NEW')][['poly_id_new','area_ha','cht_id_cur']]
        gdf_cht_new_Y_newcut = gdf_result[(gdf_result.poly_type=='CUT') & (gdf_result.cht_type=='NEW')][cols2]
        gdf_cht_new_Y_newcut['status_current'] = True
        gdf_cht_new_Y_newcut['desc'] = 'NEW-CUT_Y'
        #gdf_cht_new_Y_newcut = gdf_cht_new_Y_newcut.rename(columns={'poly_id_new': 'polygon_id', 'cht_id_cur': 'cohort_id'})
        gdf_cht_new_Y_newcut = gdf_cht_new_Y_newcut.rename(columns={'cht_id_cur': 'cohort_id'})

        #import ipdb; ipdb.set_trace()
        gdf_cht_combined = pd.concat(
            [gdf_cht_orig_Y, gdf_cht_new_Y, gdf_cht_new_N, gdf_cht_new_Y_newcut],
            ignore_index=True,      # Reset index
            sort=False              # Maintain column order
        )

        #gdf_cht_combined = gdf_cht_combined.rename(columns={'poly_id_new': 'polygon_id'})

        # Merge with sql query lookup gdf
#        gdf_cht_combined = gdf_cht_combined.merge(
#            cohort_df,
#            left_on='cohort_id',
#            right_on='cohort_id',
#            how='left'
#        )

        # update with data from cohort_get_init
        gdf_cht_combined = merge_gdfs(
            gdf_cht_combined,
            cohort_gdf_init,
            ['cohort_id', 'obj_code', 'complete_date', 'target_ba_m2ha']
        )

        gdf_cht_combined['obj_code'] = gdf_cht_combined['obj_code'].str.strip()
        #import ipdb; ipdb.set_trace()
        gdf_cht_combined = gdf_cht_combined.apply(update_columns, axis=1)
        return gdf_cht_combined

    def assemble_gdf_result(self, gdf_result, gdf_hist, cohort_id):
        '''
            # gdf_result[['polygon_id', 'poly_id_new','name', 'area_ha_orig', 'area_ha', 'compartment', 'poly_type','cht_type', 'cht_id_cur', 'cht_id_new', 'fea_id', 'obj_code', 'target_ba_']]

            1. Where the cht_type=='ORIG',
                 a. No changes necessary to assign_cht_to_ply table records, since Area already updated in Polygon table
            2. Where the cht_type=='NEW',
                 b. update/set original cohort_id's cohort.status_current to False
                 c. add new records to assign_cht_to_ply table --> link 'poly_id_new' to 'cht_id_new' (cohort.status_current=True)
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
        gdf_result.drop(columns=['index','is_sliver','sliver_ratio', 'area', 'length','intersect_area', 'overlap_perc'], inplace=True) # not reqd
        gdf_result = find_and_merge(gdf_result, self.threshold)
        gdf_result = self.add_cht_id_to_gdf_sql(gdf_result)
        gdf_result = self.classify_polygons(gdf_result, self.gdf_single, tolerance=0.95)

        # add data from shapefile attributes
        gdf_result[['fea_id', 'obj_code', 'target_ba_']] = None # initialize column
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'fea_id']     = self.gdf_single.fea_id.iloc[0]
        #import ipdb; ipdb.set_trace()
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'obj_code']   = self.gdf_single.obj_code.iloc[0]
        gdf_result.loc[gdf_result['poly_type']=='BASE', 'target_ba_'] = self.gdf_single.target_ba_.iloc[0]

        if 'index_right' in gdf_result.columns:
            gdf_result.drop('index_right', axis=1, inplace=True)

        #import ipdb; ipdb.set_trace()
        gdf_result = gdf_result.explode()
        gdf_result.reset_index(inplace=True)
        operations_summary, gdf_result = write_gdf_to_tmp_polygon(
            gdf_result=gdf_result,
            engine=self.conn_engine,
            current_user="system"
        )
        logger.info(f'\nCohort_id:  {cohort_id}')

        # Add new column cht_id_cur
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

    def _save_cht_new_to_db(self, gdf_cht_new):
        """
        Save filtered gdf_cht_new data to PostgreSQL table tmp_assign_cht_to_ply
        using pandas to_sql with ON CONFLICT handling
        Returns list of cht2ply_id that were created or updated
        """

        # Filter data for 'NEW-BASE_Y' description
        filtered_gdf = gdf_cht_new[gdf_cht_new['desc'] == 'NEW-BASE_Y'].copy()

        if filtered_gdf.empty:
            logger.info("No records found with desc='NEW-BASE_Y'. Nothing to update.")
            return []

        # Map column names and handle missing op_id
        filtered_gdf['op_id'] = filtered_gdf.get('op_id', None)

        # Convert to proper Python types
        db_data = filtered_gdf[['poly_id_new', 'cohort_id', 'op_id', 'status_current']].copy()
        db_data.columns = ['polygon_id', 'cohort_id', 'op_id', 'status_current']

        # Ensure correct data types and handle empty strings/NaN values
        db_data['polygon_id'] = pd.to_numeric(db_data['polygon_id'], errors='coerce').fillna(0).astype(int)
        db_data['cohort_id'] = pd.to_numeric(db_data['cohort_id'], errors='coerce').fillna(0).astype(int)
        db_data['status_current'] = db_data['status_current'].astype(bool)

        # Handle op_id - convert empty strings to None and then to proper integer with NaN support
        if 'op_id' in db_data.columns:
            # Replace empty strings with NaN, then convert to numeric
            db_data['op_id'] = db_data['op_id'].replace('', None)
            db_data['op_id'] = pd.to_numeric(db_data['op_id'], errors='coerce').astype('Int64')

        # Remove duplicate cohort_id values - keep the last occurrence
        db_data = db_data.drop_duplicates(subset=['cohort_id'], keep='last')

        logger.info(f"Processing {len(db_data)} unique records after removing duplicates")

        try:
            # Create temporary table
            temp_table_name = 'temp_cht_data'

            db_data.to_sql(
                temp_table_name,
                self.conn_engine,
                if_exists='replace',
                index=False
            )

            with self.conn_engine.connect() as conn:
                # Use ON CONFLICT query
                upsert_query = text("""
                    INSERT INTO tmp_assign_cht_to_ply (polygon_id, cohort_id, op_id, status_current)
                    SELECT polygon_id, cohort_id, op_id, status_current
                    FROM temp_cht_data
                    ON CONFLICT (cohort_id)
                    DO UPDATE SET
                        polygon_id = EXCLUDED.polygon_id,
                        op_id = EXCLUDED.op_id,
                        status_current = EXCLUDED.status_current
                    RETURNING cht2ply_id, cohort_id
                """)

                result = conn.execute(upsert_query)
                affected_records = result.fetchall()
                conn.commit()

                # Extract cht2ply_id from results
                cht2ply_ids = [record[0] for record in affected_records]

                # Drop temporary table
                conn.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))

                logger.info(f"Successfully upserted {len(cht2ply_ids)} records for 'NEW-BASE_Y'")
                logger.info(f"{cht2ply_ids}")

                return cht2ply_ids

        except Exception as e:
            logger.error(f"Error saving data to PostgreSQL: {str(e)}")
            raise


    def __save_cht_new_to_db(self, gdf_cht_new, user=None):
        """
        Save filtered gdf_cht_new data to db
        Returns list of cht2ply_id that were created or updated
        """

        # Filter data for 'NEW-BASE_Y' description
        filtered_gdf = gdf_cht_new[gdf_cht_new['desc'] == 'NEW-BASE_Y'].copy()

        if filtered_gdf.empty:
            logger.info("No records found with desc='NEW-BASE_Y'. Nothing to update.")
            return []

        # Map column names and handle missing op_id
        filtered_gdf['op_id'] = filtered_gdf.get('op_id', None)

        # Convert to proper Python types
        db_data = filtered_gdf[['poly_id_new', 'cohort_id', 'op_id', 'status_current']].copy()
        db_data.columns = ['polygon_id', 'cohort_id', 'op_id', 'status_current']

        # Ensure correct data types
        db_data['polygon_id'] = pd.to_numeric(db_data['polygon_id'], errors='coerce').fillna(0).astype(int)
        db_data['cohort_id'] = pd.to_numeric(db_data['cohort_id'], errors='coerce').fillna(0).astype(int)
        db_data['status_current'] = db_data['status_current'].astype(bool)

        # Handle op_id
        if 'op_id' in db_data.columns:
            db_data['op_id'] = db_data['op_id'].replace('', None)
            db_data['op_id'] = pd.to_numeric(db_data['op_id'], errors='coerce').astype('Int64')

        # Remove duplicate cohort_id values
        db_data = db_data.drop_duplicates(subset=['cohort_id'], keep='last')

        cht2ply_ids = []
        current_time = timezone.now()
        username = user.username if user else 'system'

        try:
            for _, row in db_data.iterrows():
                # Try to get existing record
                try:
                    obj, created = TmpAssignChtToPly.objects.get_or_create(
                        cohort_id=row['cohort_id'],
                        defaults={
                            'polygon_id': row['polygon_id'],
                            'op_id': row['op_id'],
                            'status_current': row['status_current'],
                            'created_on': current_time,
                            'created_by': username,
                            'updated_on': current_time,
                            'updated_by': username,
                        }
                    )

                    if not created:
                        # Update existing record
                        obj.polygon_id = row['polygon_id']
                        obj.op_id = row['op_id']
                        obj.status_current = row['status_current']
                        obj.updated_on = current_time
                        obj.updated_by = username
                        obj.save()

                    cht2ply_ids.append(obj.cht2ply_id)

                except Exception as e:
                    logger.error(f"Error processing cohort_id {row['cohort_id']}: {str(e)}")
                    continue

            logger.info(f"Successfully processed {len(cht2ply_ids)} records for 'NEW-BASE_Y'")
            return cht2ply_ids

        except Exception as e:
            logger.error(f"Error saving data to PostgreSQL: {str(e)}")
            raise

    def save_cht_new_to_db(self, gdf_cht_new, user=None):
        """
        Version using Django ORM with proper model import and NA value handling
        """

        # Import the model dynamically to avoid circular imports
        #tmp_assign_cht_to_ply = apps.get_model('your_app_name', 'tmp_assign_cht_to_ply')
        from silrec.components.forest_blocks.models import TmpAssignChtToPly

        # Filter data for 'NEW-BASE_Y' description
        filtered_gdf = gdf_cht_new[gdf_cht_new['desc'] == 'NEW-BASE_Y'].copy()

        if filtered_gdf.empty:
            logger.info("No records found with desc='NEW-BASE_Y'. Nothing to update.")
            return []

        logger.info(f"Found {len(filtered_gdf)} records with 'NEW-BASE_Y'")

        # Map column names and handle missing op_id
        filtered_gdf['op_id'] = filtered_gdf.get('op_id', None)

        # Convert to proper Python types
        db_data = filtered_gdf[['poly_id_new', 'cohort_id', 'op_id', 'status_current']].copy()
        db_data.columns = ['polygon_id', 'cohort_id', 'op_id', 'status_current']

        # Ensure correct data types
        db_data['polygon_id'] = pd.to_numeric(db_data['polygon_id'], errors='coerce').fillna(0).astype(int)
        db_data['cohort_id'] = pd.to_numeric(db_data['cohort_id'], errors='coerce').fillna(0).astype(int)

        # Handle op_id - convert pandas NA to None
        if 'op_id' in db_data.columns:
            db_data['op_id'] = db_data['op_id'].replace('', None)
            db_data['op_id'] = pd.to_numeric(db_data['op_id'], errors='coerce').astype('Int64')
            # Convert pandas Int64 NA to Python None
            db_data['op_id'] = db_data['op_id'].where(db_data['op_id'].notna(), None)

        # Handle status_current
        db_data['status_current'] = db_data['status_current'].fillna(False)
        db_data['status_current'] = db_data['status_current'].astype(bool)

        # Remove duplicate cohort_id values
        initial_count = len(db_data)
        db_data = db_data.drop_duplicates(subset=['cohort_id'], keep='last')
        duplicate_count = initial_count - len(db_data)
        if duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate cohort_id records")

        cht2ply_ids = []
        current_time = timezone.now()
        username = user.username if user else 'system'
        success_count = 0
        error_count = 0

        try:
            for index, row in db_data.iterrows():
                try:
                    # Convert all values to native Python types
                    polygon_id = int(row['polygon_id'])
                    cohort_id = int(row['cohort_id'])

                    # Handle op_id - convert pandas NA to None explicitly
                    op_id = row['op_id']
                    if pd.isna(op_id) or op_id is None:
                        op_id = None
                    else:
                        op_id = int(op_id)

                    status_current = bool(row['status_current'])

                    logger.info(f"Processing cohort_id {cohort_id}: polygon_id={polygon_id}, op_id={op_id}, status_current={status_current}")

                    # Try to get existing record
                    obj, created = TmpAssignChtToPly.objects.get_or_create(
                        cohort_id=cohort_id,
                        defaults={
                            'polygon_id': polygon_id,
                            'op_id': op_id,
                            'status_current': status_current,
                            'created_on': current_time,
                            'created_by': username,
                            'updated_on': current_time,
                            'updated_by': username,
                        }
                    )

                    if not created:
                        # Update existing record
                        obj.polygon_id = polygon_id
                        obj.op_id = op_id
                        obj.status_current = status_current
                        obj.updated_on = current_time
                        obj.updated_by = username
                        obj.save()
                        action = "updated"
                    else:
                        action = "created"

                    cht2ply_ids.append(obj.cht2ply_id)
                    success_count += 1
                    logger.info(f"Successfully {action} record for cohort_id {cohort_id} (cht2ply_id: {obj.cht2ply_id})")

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing cohort_id {row['cohort_id']}: {str(e)}")
                    logger.error(f"Problematic row data: polygon_id={row['polygon_id']}, cohort_id={row['cohort_id']}, op_id={row['op_id']}, status_current={row['status_current']}")
                    # Log the full traceback for debugging
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue

            logger.info(f"Successfully processed {success_count} records, {error_count} errors for 'NEW-BASE_Y'")
            return cht2ply_ids

        except Exception as e:
            logger.error(f"Error saving data to PostgreSQL: {str(e)}")
            raise

