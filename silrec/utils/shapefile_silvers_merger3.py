from django.conf import settings
from django.db import models
from sqlalchemy import create_engine
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union, polygonize

import json
from silrec.utils.plot_utils import plot_gdf as plot
from silrec.utils.plot_utils import plot_overlay, plot_multi
from silrec.utils.sliver_test1 import identify_slivers
from silrec.components.proposals.models import PolygonHistory

import matplotlib as mpl
mpl.use('TkAgg')
#matplotlib.use('GTKAgg')
#matplotlib.use('Agg')



class ShapefileSliversMerger():
    '''
    import geopandas as gpd
    from silrec.utils.shapefile_silvers_merger3 import ShapefileSliversMerger

    gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
    gdf_shp.to_crs('EPSG:28350', inplace=True)
    ssm = ShapefileSliversMerger(gdf_shp, proposal_id=1)
    gdf_result = ssm.create_gdf()

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


    '''
    def __init__(self, gdf_shpfile, proposal_id, threshold=None, sql_polygons=None):
        self.gdf_shpfile = gdf_shpfile
        self.proposal_id = proposal_id
        self.threshold = threshold
        self.conn_engine = self.get_conn_engine()
        self.gdf_hist_polygons_total = self.get_polygons_gdf(gdf_shpfile, 'polygon', sql_polygons)

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
        '''
        dbschema='silrec,public' # Searches left-to-right
        engine = create_engine(
            'postgresql://dev:dev123@localhost:5432/silrec_test1',
            connect_args={'options': '-c search_path={}'.format(dbschema)}
        )
        return engine

    @property
    def next_version_id(self):
        version_id = PolygonHistory.objects.filter(proposal_id=self.proposal_id).aggregate(models.Max('version_id'))['version_id__max']
        return version_id + 1 if version_id is not None else 0

    def save_global_intersecting_polygons(self, gdf, table_name='silrec_polygonhistory'):
        ''' Save all polygons from forest_blocks.polygon (to PolygonHistory) that intersect the global (input) shapefile '''
        gdf.to_postgis(table_name, con=self.conn_engine, if_exists='append', schema='silrec')

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

            sql = f'''SELECT ph.polygon_id, ph.name, ph.geom FROM {table_name} AS ph WHERE ph.closed IS NULL AND ST_Intersects(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'));'''

        gdf = gpd.read_postgis(sql, con=self.conn_engine, geom_col='geom')

        gdf['version_id'] = self.next_version_id
        gdf['proposal_id'] = self.proposal_id
        gdf.rename(columns={'polygon_id': 'polygon_src_id'}, inplace=True)

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

        return gpd.sjoin(gdf_common_boundary, centroids_df, how="inner", predicate="intersects")

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
    #    import geopandas as gpd
    #    from silrec.components.main.utils import polygons_to_gdf
    #    #polygons = polygons_to_gdf()

        def get_base_polygon_id(row):
            ''' for given split polygon, returns the polygon_id of the parent (historical polygons gdf) polygon
                usage: gdf_tmp['polygon_id'] = gdf_tmp.apply(get_base_polygon_id, axis=1)
                --> Returns the parent polygon_id (intersected by the centroid - representative_point() falls inside the polygon)
            '''
            # Convert Centroid POINT to GDF
            #import ipdb; ipdb.set_trace()
            centroid_point = row.geometry.representative_point()
            data = {'geometry': [centroid_point]}
            centroid_gdf = gpd.GeoDataFrame(data, geometry='geometry', crs=settings.CRS_GDA94)

            if 'index_right' in self.gdf_hist_polygons_total.columns:
                self.polygons.drop(['index_right'], axis=1, inplace=True)

            gdf = gpd.sjoin(self.gdf_hist_polygons_total, centroid_gdf, how="inner", predicate="intersects")
            return None if gdf.empty else gdf.polygon_src_id.iloc[0]

#        import ipdb; ipdb.set_trace()
#        self.save_global_intersecting_polygons(self.gdf_hist_polygons_total, 'silrec_polygonhistory')

        #for index, row in self.gdf_shpfile.iloc[::-1].iterrows():
        #gdf_result = gpd.GeoDataFrame()
        for index, row in self.gdf_shpfile.iterrows():
            gdf_single = gpd.GeoDataFrame([row], geometry=[row.geometry], crs=settings.CRS_GDA94)
            #gdf_single = gpd.read_file('silrec/utils/Shapefiles/demarcation_1_polygons/Demarcation_Boundary_1_polygons.shp')

            # Determine which geometries in polygons geodataframe intersect with any geometry in gdf_single
            # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
            intersects_mask_single = self.gdf_hist_polygons_total.geometry.intersects(self.gdf_shpfile.unary_union)
            gdf_polygons_intersecting_single = self.gdf_hist_polygons_total[intersects_mask_single]

            # non overlapping overlayed geometries (creates independent partitioned geometries)
            self.gdf_polygons_partitioned = gpd.overlay(gdf_single, gdf_polygons_intersecting_single, how='union')

            #import ipdb; ipdb.set_trace()
            base_polygon = self.get_base_polygon_gdf(gdf_single, self.gdf_polygons_partitioned)


            threshold = self.threshold if self.threshold else settings.SLIVER_AREALENGTH_THRESHOLD
            gdf_slivers = identify_slivers(self.gdf_polygons_partitioned.explode(), base_polygon, sliver_threshold=threshold) # better since returns all slivers touching base_polygon
            mask = self.gdf_polygons_partitioned.explode().geometry.area/self.gdf_polygons_partitioned.explode().geometry.length < threshold
            gdf_excl_slivers = self.gdf_polygons_partitioned.explode()[~(mask)]
            gdf_slivers_plus_base = gpd.GeoDataFrame(pd.concat([gdf_slivers, base_polygon], ignore_index=True))

            gdf_excl_slivers_plus_base = gpd.overlay(self.gdf_polygons_partitioned, gdf_slivers_plus_base, how='difference')
            gdf_excl_slivers_plus_base['origin'] = 'HIST'
            gdf_slivers_merged = gdf_slivers_plus_base.dissolve()
            gdf_slivers_merged['origin'] = 'BASE'
            gdf_result = gpd.GeoDataFrame(pd.concat([gdf_excl_slivers_plus_base, gdf_slivers_merged], ignore_index=True))
            gdf_result = gdf_result[gdf_result.area>1] # drop tiny areas

            gdf_result['poly_src_id'] = gdf_result.apply(get_base_polygon_id, axis=1) # add column for the corresponding hist polygon_id
            gdf_result['poly_src_id'] = gdf_result['poly_src_id'].fillna(0).astype(int)

            if 'index_right' in gdf_result.columns:
                gdf_result.drop('index_right', axis=1, inplace=True)

            # identify the 'cookie-cut' polygons
            gdf_within = gpd.sjoin(self.gdf_polygons_partitioned, gdf_result, how="inner", predicate="within")
            gdf_within_not = gpd.overlay(self.gdf_polygons_partitioned, gdf_within, how='difference')                           # with indices from self.gdf_result
            gdf_within_not_with_idx = gpd.sjoin(gdf_result, gdf_within_not, how="inner", predicate="within") # with indices from self.gdf_polygons_partitioned
            indices = gdf_within_not_with_idx.index.to_list()
            gdf_result.loc[indices,'origin'] = 'CUT'

            #gdf_result_filtered = gdf_result[['poly_src_id', 'name', 'geometry']]
            gdf_result_filtered = gdf_result[['poly_src_id', 'origin', 'geometry']]
            gdf_result_filtered['version_id'] = self.next_version_id
            gdf_result_filtered['proposal_id'] = self.proposal_id
            #plot_multi([gdf_result_filtered, gdf_result_filtered], use_random_cols=False)
            import ipdb; ipdb.set_trace()
            pass

            #self.save_global_intersecting_polygons(gdf_result_filtered, 'silrec_polygonhistory')

        return gdf_result

#    def processed_to_json_obj(self):
#        data = {}
#        data["hist_polygons_intersecting"] = json.loads(self.hist_polygons_intersecting_to_json())
#        data["base_polygon"] = json.loads(self.base_polygon_to_json())
#        data["overlay"] = json.loads(self.overlay_to_json())
#        data["result"] = json.loads(self.result_to_json())
#
#        return data
#
#    def hist_polygons_intersecting_to_json(self):
#        ''' Historical Polygons ('active') from silrec_v3 tha intersect with base_polygon '''
#        self.gdf_polygons_intersecting_single[['created_on','updated_on']] = self.polygons_intersecting_single[['created_on','updated_on']].astype(str)
#        return self.gdf_polygons_intersecting_single.to_json()
#
#    def base_polygon_to_json(self, gdf):
#        ''' The original polygon from the uploaded shapefile '''
#        #gdf_single[['created_on','updated_on']] = gdf_single[['created_on','updated_on']].astype(str)
#        return gdf.to_json()
#
#    def overlay_to_json(self):
#        ''' Overlay prior to slivers being merged '''
#        self.gdf_overlay[['created_on','updated_on']] = self.gdf_overlay[['created_on','updated_on']].astype(str)
#        return self.gdf_overlay.to_json()
#
#    def result_to_json(self):
#        ''' Overlay after slivers have been merged '''
#        #self.gdf_result[['created_on','updated_on']] = self.gdf_result[['created_on','updated_on']].astype(str)
#        return self.gdf_result.to_json()
#
#    @property
#    def plot_gdf_single(self, gdf):
#        plot_gdf(gdf_single)
#
#    @property
#    def plot_hist_polygons(self):
#        plot_gdf(self.gdf_polygons_intersecting_single)
#
#    @property
#    def plot_overlay(self):
#        plot_gdf(self.gdf_overlay)
#
#    @property
#    def plot_slivers(self):
#        plot_gdf(self.gdf_slivers)
#
#    @property
#    def plot_slivers_plus_base(self):
#        plot_gdf(self.gdf_slivers_plus_base)
#
#    @property
#    def plot_slivers_merged(self):
#        plot_gdf(self.gdf_slivers_merged)
#
#    @property
#    def plot_hist_polygons_new(self):
#        plot_gdf(self.gdf_new_hist_polygons)
#
#    @property
#    def plot_result(self):
#        plot_gdf(self.gdf_result)




