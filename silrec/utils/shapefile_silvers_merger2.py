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
from silrec.utils.plot_utils import plot_gdf, plot_overlay
from silrec.components.proposals.models import PolygonHistory

import matplotlib as mpl
mpl.use('TkAgg')
#matplotlib.use('GTKAgg')
#matplotlib.use('Agg')



class ShapefileSliversMerger():
    '''
    import geopandas as gpd
    from silrec.utils.shapefile_silvers_merger2 import ShapefileSliversMerger

    gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
    gdf_shp.to_crs('EPSG:28350', inplace=True)
    ssm = ShapefileSliversMerger(gdf_shp)
    gdf_result = ssm.create_gdf()

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
    def __init__(self, gdf_global, proposal_id, threshold=None, sql_polygons=None):
        #self.gdf_global = gdf_global
        self.proposal_id = proposal_id
        self.threshold = threshold
        self.conn_engine = self.get_conn_engine()
        self.gdf_polygons_global = self.get_polygons_gdf(gdf_global, 'polygon', sql_polygons)

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
        version_id = PolygonHistory.objects.filter(proposal_id=self.proposal_id).aggregate(models.Max('version_id'))['version_id__max'] + 1
        return version_id if version_id is not None else 0

    def save_global_intersecting_polygons(self, gdf, table_name='silrec_polygonhistory'):
        ''' Save the all polygons from forest_blocks.polygon (to PolygonHistory) that intersect the global shapefile '''
        gdf.to_postgis(table_name, con=self.conn_engine, if_exists='append', schema='silrec')

    def get_polygons_gdf(self, gdf, table_name, sql=None):
        ''' Get intersecting polygons from forest_blocks.polygon - intersecting with the given base polygon

            Returns --> SQL query result as gdf
        '''

        if not sql:
            srid = 'SRID=' + settings.CRS_GDA94.split(':')[1] + '; ' # SRID=28350;
            base_polygon_wkt = srid + gdf.dissolve().iloc[0].geometry.wkt
            sql = f'''SELECT ph.polygon_id, ph.name, ph.geom FROM {table_name} AS ph WHERE ph.closed IS NULL AND ST_Intersects(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'));'''

        #import ipdb; ipdb.set_trace()
        self.gdf = gpd.read_postgis(sql, con=self.conn_engine, geom_col='geom')

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
        centroids_gdf1 = gdf_base.geometry.centroid
        centroids_df = gpd.GeoDataFrame(geometry=centroids_gdf1)

        if 'index_right' in gdf_common_boundary.columns:
            gdf_common_boundary.drop(['index_right'], axis=1, inplace=True)

        return gpd.sjoin(gdf_common_boundary, centroids_df, how="inner", predicate="intersects")

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
                --> Returns the parent polygon_id (intersected by the centroid)
            '''
            # Convert Centroid POINT to GDF
            import ipdb; ipdb.set_trace()
            centroid_point = row.geometry.centroid
            data = {'geometry': [centroid_point]}
            centroid_gdf = gpd.GeoDataFrame(data, geometry='geometry', crs=settings.CRS_GDA94)

            if 'index_right' in self.gdf_polygons_global.columns:
                self.polygons.drop(['index_right'], axis=1, inplace=True)

            gdf = gpd.sjoin(self.gdf_polygons_global, centroid_gdf, how="inner", predicate="intersects")
            return None if gdf.empty else gdf.polygon_src_id.iloc[0]

#        import ipdb; ipdb.set_trace()
#        self.save_global_intersecting_polygons(self.gdf_polygons_global, 'silrec_polygonhistory')

        for index, row in self.gdf_polygons_global.iterrows():
            gdf_single = gpd.GeoDataFrame([row], geometry=[row.geometry], crs=settings.CRS_GDA94)
            # Determine which geometries in polygons geodataframe intersect with any geometry in gdf_single
            intersects_mask_single = self.gdf_polygons_global.geometry.intersects(gdf_single.unary_union)

            # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
            gdf_polygons_intersecting_single = self.gdf_polygons_global[intersects_mask_single]

            # plot the boundary outlines only (of all polygons touching also)
            bound_single = unary_union(gdf_polygons_intersecting_single.geometry.boundary)
            boundary_single = gpd.GeoSeries([bound_single])

            # non overlapping overlayed geometries (creates independent partitioned geometries)
            self.gdf_overlay = gpd.overlay(gdf_single, gdf_polygons_intersecting_single, how='union')

            # plot the boundary outlines only (of all polygons touching also)
            bound_overlay = unary_union(self.gdf_overlay.geometry.boundary)
            boundary_overlay = gpd.GeoSeries([bound_overlay])
            poly_list = list(polygonize(bound_overlay)) #Create polygons from it
            gdf_split = gpd.GeoDataFrame(geometry=poly_list) #And a dataframe
            import ipdb; ipdb.set_trace()
            gdf_split.set_crs(settings.CRS_GDA94, inplace=True)

            # Perform the spatial join
            # This will find all geometries in gdf1 that intersect with gdf2
            # (i.e., touch at a point, line, or boundary)
            #gdf_common_boundary = gpd.sjoin(gdf_split, gdf_split.iloc[[2]], how='inner', predicate='intersects')
            gdf_common_boundary = gpd.sjoin(gdf_split, gdf_single, how='inner', predicate='intersects')

            # get the gdf_single split equivalent from gdf_common_boundary
            base_polygon = self.get_base_polygon_gdf(gdf_single, gdf_common_boundary)

            threshold = self.threshold if self.threshold else settings.SLIVER_AREALENGTH_THRESHOLD
            gdf_slivers = gdf_common_boundary[gdf_common_boundary.geometry.area/gdf_common_boundary.geometry.length < threshold]
            gdf_slivers_plus_base = gpd.GeoDataFrame(pd.concat([gdf_slivers, base_polygon], ignore_index=True))

            # all new historical polygons that intersect, excluding slivers and base polygon (gdf_single)
            #gdf_new_hist_polygons = gdf_common_boundary[~gdf_slivers_plus_base.geometry.contains(gdf_common_boundary.geometry)]
            gdf_new_hist_polygons = gpd.overlay(gdf_common_boundary, gdf_slivers_plus_base, how='difference')
            gdf_new_hist_polygons['origin'] = 'HIST'

            # View the plots - the sum of the two below make-up 'gdf_common_boundary'
            # plot_gdf(gdf_new_hist_polygons) # Everything excluding slivers + base_polygon
            # plot_gdf(gdf_slivers_plus_base) # Only slivers + base_polygon

            gdf_slivers_merged = gdf_slivers_plus_base.dissolve() # Multipolygon
            gdf_slivers_merged['origin'] = 'BASE'

            #gdf_slivers_merged = gdf_slivers_plus_base.dissolve().explode()) # Polygon(s) - >1 if there gaps between polygons preventing merge to a single polygon
            #import ipdb; ipdb.set_trace()
            gdf_result = gpd.GeoDataFrame()
            gdf_result = gpd.GeoDataFrame(pd.concat([gdf_slivers_merged, gdf_new_hist_polygons], ignore_index=True))
            #gdf_result['polygon_id'] = self.gdf_result.apply(get_base_polygon_id, args=(self.gdf_result, self.polygons), axis=1)
            gdf_result['polygon_id'] = gdf_result.apply(get_base_polygon_id, axis=1) # add column for the corresponding hist polygon_id
            gdf_result['Area'] = gdf_result.area # update the area column
            import ipdb; ipdb.set_trace()

            #plot_overlay(gdf_five, polygons_intersecting_five)
            if 'index_right' in gdf_result.columns:
                gdf_result.drop('index_right', axis=1, inplace=True)

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


