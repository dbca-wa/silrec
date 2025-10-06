from django.conf import settings
from sqlalchemy import create_engine
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union, polygonize

import json
from silrec.utils.plot_utils import plot_gdf, plot_overlay, plot_multi

import matplotlib as mpl
mpl.use('TkAgg')
#matplotlib.use('GTKAgg')
#matplotlib.use('Agg')

class ShapefileSliversMerger():
    '''
    import geopandas as gpd
    from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger

    gdf_single = gpd.read_file('silrec/utils/Shapefiles/demarcation_single/demarcation_single_feature.shp')
    gdf_single.to_crs('EPSG:28350', inplace=True)
    ssm = ShapefileSliversMerger(gdf_single)
    gdf_result = ssm.create_gdf()

    ssm.plot_hist_polygons
    ssm.plot_hist_polygons_new
    ssm.plot_overlay
    ssm.plot_slivers
    ssm.plot_slivers_plus_base
    ssm.plot_slivers_merged
    ssm.plot_result
    '''
    def __init__(self, gdf_single, threshold=None, sql_polygons=None):
        self.gdf_single = gdf_single
        self.threshold = threshold
        self.conn_engine = self.get_conn_engine()
        self.polygons = self.get_polygons_gdf(sql_polygons)

        # for plots
        self.polygons_intersecting_single = None
        self.gdf_overlay = None
        self.gdf_slivers = None
        self.gdf_slivers_plus_base = None
        self.gdf_slivers_merged = None
        self.gdf_new_hist_polygons = None
        self.gdf_result = None

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

    def get_polygons_gdf(self, sql_polygons):
        sql = sql_polygons if sql_polygons else 'select * from polygon;'
        return gpd.read_postgis(sql, con=self.conn_engine, geom_col='geom')

#    def get_polygons_gdf(self, gdf, table_name, sql=None):
#        ''' Get intersecting polygons from forest_blocks.polygon - intersecting with the given base polygon
#            Returns --> SQL query result as gdf
#        '''
#        import ipdb; ipdb.set_trace()
#        if not sql:
#            srid = 'SRID=' + settings.CRS_GDA94.split(':')[1] + '; ' # SRID=28350;
#            combined_geometry = unary_union(gdf['geometry'])
#            base_polygon_wkt = srid + combined_geometry.wkt
#            sql = f'''SELECT ph.polygon_id, ph.name, ph.geom FROM {table_name} AS ph WHERE ph.closed IS NULL AND ST_Intersects(ph.geom, ST_GeomFromEWKT('{base_polygon_wkt}'));'''
#
#        gdf = gpd.read_postgis(sql, con=self.conn_engine, geom_col='geom')
#        return gdf


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
        polygons, gdf_single, polygons_intersecting_single, gdf_overlay, gdf_split, gdf_common_boundary, gdf_slivers, base_polygon, gdf_slivers_plus_base, gdf_new_hist_polygons, gdf_slivers_merged, gdf_result

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
            centroid_point = row.geometry.centroid
            data = {'geometry': [centroid_point]}
            centroid_gdf = gpd.GeoDataFrame(data, geometry='geometry', crs=settings.CRS_GDA94)

            if 'index_right' in self.polygons.columns:
                self.polygons.drop(['index_right'], axis=1, inplace=True)

            gdf = gpd.sjoin(self.polygons, centroid_gdf, how="inner", predicate="intersects")
            return None if gdf.empty else gdf.polygon_id.iloc[0]



    #    sql='select * from polygon;'
    #    polygons = gpd.read_postgis(sql, con=get_conn_engine(), geom_col='geom')

    #    gdf_single = gpd.read_file('silrec/utils/Shapefiles/demarcation_single/demarcation_single_feature.shp')
    #    gdf_single.to_crs('EPSG:28350', inplace=True)
    #
    #    gdf_five = gpd.read_file('silrec/utils/Shapefiles/demarcation_five/demarcation_five_features.shp')
    #    gdf_five.to_crs('EPSG:28350', inplace=True)

        # res = gdf_single.overlay(polygons, how='intersection')

        # Determine which geometries in polygons geodataframe intersect with any geometry in gdf_single
        # This creates a boolean Series
        intersects_mask_single = self.polygons.geometry.intersects(self.gdf_single.unary_union)
    #    intersects_mask_five   = polygons.geometry.intersects(gdf_five.unary_union)

        # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
        self.polygons_intersecting_single = self.polygons[intersects_mask_single]
    #    polygons_intersecting_five = polygons[intersects_mask_five]

        # plot the boundary outlines only (of all polygons touching also)
        bound_single = unary_union(self.polygons_intersecting_single.geometry.boundary)
        boundary_single = gpd.GeoSeries([bound_single])

        #import ipdb; ipdb.set_trace()
        # non overlapping overlayed geometries (creates independent partitioned geometries)
        self.gdf_overlay = gpd.overlay(self.gdf_single, self.polygons_intersecting_single, how='union')

        # plot the boundary outlines only (of all polygons touching also)
        bound_overlay = unary_union(self.gdf_overlay.geometry.boundary)
        boundary_overlay = gpd.GeoSeries([bound_overlay])
        #boundary_overlay.plot()
        poly_list = list(polygonize(bound_overlay)) #Create polygons from it
        gdf_split = gpd.GeoDataFrame(geometry=poly_list) #And a dataframe
        #import ipdb; ipdb.set_trace()
        gdf_split.set_crs(settings.CRS_GDA94, inplace=True)

        # Perform the spatial join
        # This will find all geometries in gdf1 that intersect with gdf2
        # (i.e., touch at a point, line, or boundary)
        #gdf_common_boundary = gpd.sjoin(gdf_split, gdf_split.iloc[[2]], how='inner', predicate='intersects')
        gdf_common_boundary = gpd.sjoin(gdf_split, self.gdf_single, how='inner', predicate='intersects')
        self.gdf = gdf_common_boundary.copy() # net split

        # get the gdf_single split equivalent from gdf_common_boundary
        base_polygon = self.get_base_polygon_gdf(self.gdf_single, gdf_common_boundary)

        threshold = self.threshold if self.threshold else settings.SLIVER_AREALENGTH_THRESHOLD
        self.gdf_slivers = gdf_common_boundary[gdf_common_boundary.geometry.area/gdf_common_boundary.geometry.length < threshold]
        self.gdf_slivers_plus_base = gpd.GeoDataFrame(pd.concat([self.gdf_slivers, base_polygon], ignore_index=True))

        # all new historical polygons that intersect, excluding slivers and base polygon (gdf_single)
        #gdf_new_hist_polygons = gdf_common_boundary[~gdf_slivers_plus_base.geometry.contains(gdf_common_boundary.geometry)]
        self.gdf_new_hist_polygons = gpd.overlay(gdf_common_boundary, self.gdf_slivers_plus_base, how='difference')
        self.gdf_new_hist_polygons['origin'] = 'HIST'

        # View the plots - the sum of the two below make-up 'gdf_common_boundary'
        # plot_gdf(gdf_new_hist_polygons) # Everything excluding slivers + base_polygon
        # plot_gdf(gdf_slivers_plus_base) # Only slivers + base_polygon

        self.gdf_slivers_merged = self.gdf_slivers_plus_base.dissolve() # Multipolygon
        self.gdf_slivers_merged['origin'] = 'BASE'

        #gdf_slivers_merged = gdf_slivers_plus_base.dissolve().explode()) # Polygon(s) - >1 if there gaps between polygons preventing merge to a single polygon
        #import ipdb; ipdb.set_trace()
        self.gdf_result = gpd.GeoDataFrame(pd.concat([self.gdf_slivers_merged, self.gdf_new_hist_polygons], ignore_index=True))
        #gdf_result['polygon_id'] = self.gdf_result.apply(get_base_polygon_id, args=(self.gdf_result, self.polygons), axis=1)
        self.gdf_result['polygon_id'] = self.gdf_result.apply(get_base_polygon_id, axis=1) # add column for the corresponding hist polygon_id
        self.gdf_result['Area'] = self.gdf_result.area # update the area column

        #plot_overlay(gdf_five, polygons_intersecting_five)
    #    return polygons, gdf_single, polygons_intersecting_single, gdf_overlay, gdf_split, gdf_common_boundary, \
    #           gdf_slivers,base_polygon, gdf_slivers_plus_base, gdf_new_hist_polygons, gdf_slivers_merged, gdf_result
        if 'index_right' in self.gdf_result.columns:
            self.gdf_result.drop('index_right', axis=1, inplace=True)

        return self.gdf_result

    def processed_to_json_obj(self):
        data = {}
        data["hist_polygons_intersecting"] = json.loads(self.hist_polygons_intersecting_to_json())
        data["base_polygon"] = json.loads(self.base_polygon_to_json())
        data["overlay"] = json.loads(self.overlay_to_json())
        data["result"] = json.loads(self.result_to_json())

        return data

    def hist_polygons_intersecting_to_json(self):
        ''' Historical Polygons ('active') from silrec_v3 tha intersect with base_polygon '''
        self.polygons_intersecting_single[['created_on','updated_on']] = self.polygons_intersecting_single[['created_on','updated_on']].astype(str)
        return self.polygons_intersecting_single.to_json()

    def base_polygon_to_json(self):
        ''' The original polygon from the uploaded shapefile '''
        #self.gdf_single[['created_on','updated_on']] = self.gdf_single[['created_on','updated_on']].astype(str)
        return self.gdf_single.to_json()

    def overlay_to_json(self):
        ''' Overlay prior to slivers being merged '''
        self.gdf_overlay[['created_on','updated_on']] = self.gdf_overlay[['created_on','updated_on']].astype(str)
        return self.gdf_overlay.to_json()

    def result_to_json(self):
        ''' Overlay after slivers have been merged '''
        #self.gdf_result[['created_on','updated_on']] = self.gdf_result[['created_on','updated_on']].astype(str)
        return self.gdf_result.to_json()

    @property
    def plot_gdf_single(self):
        plot_gdf(self.gdf_single)

    @property
    def plot_hist_polygons(self):
        plot_gdf(self.polygons_intersecting_single)
        #self.polygons_intersecting_single.plot()

    @property
    def plot_overlay(self):
        plot_gdf(self.gdf_overlay.explode())

    @property
    def plot_slivers(self):
        plot_gdf(self.gdf_slivers)

    @property
    def plot_slivers_plus_base(self):
        plot_gdf(self.gdf_slivers_plus_base)

    @property
    def plot_slivers_merged(self):
        plot_gdf(self.gdf_slivers_merged)

    @property
    def plot_hist_polygons_new(self):
        plot_gdf(self.gdf_new_hist_polygons)

    @property
    def plot_result(self):
        plot_gdf(self.gdf_result)

    @property
    def plot_multi(self):
        gdf_full = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
        gdf_full.to_crs('EPSG:28350', inplace=True)
        plot_multi([self.gdf_single, self.polygons_intersecting_single, self.gdf_common_boundary, self.gdf_slivers_plus_base, self.gdf_slivers_merged, self.gdf_result])
