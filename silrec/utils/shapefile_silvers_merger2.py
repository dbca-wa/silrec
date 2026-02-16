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
from silrec.components.proposals.models import PolygonHistory

import matplotlib as mpl
# mpl.use('TkAgg')
#matplotlib.use('GTKAgg')
#matplotlib.use('Agg')



class ShapefileSliversMerger():
    '''
    import geopandas as gpd
    from silrec.utils.shapefile_silvers_merger2 import ShapefileSliversMerger

    gdf_shp = gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
    gdf_shp.to_crs('EPSG:28350', inplace=True)
    ssm = ShapefileSliversMerger(gdf_shp, proposal_id=1)
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

        import ipdb; ipdb.set_trace()
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
        centroids_gdf1 = gdf_base.geometry.centroid
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
                --> Returns the parent polygon_id (intersected by the centroid)
            '''
            # Convert Centroid POINT to GDF
            #import ipdb; ipdb.set_trace()
            centroid_point = row.geometry.centroid
            data = {'geometry': [centroid_point]}
            centroid_gdf = gpd.GeoDataFrame(data, geometry='geometry', crs=settings.CRS_GDA94)

            if 'index_right' in self.gdf_hist_polygons_total.columns:
                self.polygons.drop(['index_right'], axis=1, inplace=True)

            gdf = gpd.sjoin(self.gdf_hist_polygons_total, centroid_gdf, how="inner", predicate="intersects")
            return None if gdf.empty else gdf.polygon_src_id.iloc[0]

#        import ipdb; ipdb.set_trace()
#        self.save_global_intersecting_polygons(self.gdf_hist_polygons_total, 'silrec_polygonhistory')

        #for index, row in self.gdf_shpfile.iloc[::-1].iterrows():
        for index, row in self.gdf_shpfile.iterrows():
            #gdf_single = gpd.GeoDataFrame([row], geometry=[row.geometry], crs=settings.CRS_GDA94)
            gdf_single = gpd.read_file('silrec/utils/Shapefiles/demarcation_1_polygons/Demarcation_Boundary_1_polygons.shp')

            # Determine which geometries in polygons geodataframe intersect with any geometry in gdf_single
            # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
#            intersects_mask_single = self.gdf_hist_polygons_total.geometry.intersects(gdf_single.unary_union)
            intersects_mask_single = self.gdf_hist_polygons_total.geometry.intersects(self.gdf_shpfile.unary_union)
            gdf_polygons_intersecting_single = self.gdf_hist_polygons_total[intersects_mask_single]
#            gdf_polygons_intersecting_single = self.gdf_shpfile.copy()

            # splits the gdf_polygons_interecting_single (from silrec_v3) into  new parts, but excludes gdf_single+slivers
            gdf_polygons_split_excl = gpd.overlay(gdf_single, gdf_polygons_intersecting_single, how='symmetric_difference')

            # base_polygon + slivers --> merged to a single polygon
            gdf_slivers_plus_base = gpd.overlay(gdf_single, gdf_polygons_intersecting_single, how='intersection')
            gdf_slivers_merged = self.merge_touching(gdf_slivers_plus_base)

            combined_gdf = gpd.GeoDataFrame(
                pd.concat([gdf_polygons_split_excl, gdf_slivers_merged], ignore_index=True),
                crs=gdf_polygons_intersecting_single.crs
            )

            # plot the boundary outlines only (of all polygons touching also)
            #bound_single = unary_union(gdf_polygons_intersecting_single.geometry.boundary)
            #boundary_single = gpd.GeoSeries([bound_single])

            # non overlapping overlayed geometries (creates independent partitioned geometries)
            self.gdf_polygons_partitioned = gpd.overlay(gdf_single, gdf_polygons_intersecting_single, how='union')

            import ipdb; ipdb.set_trace()
            # plot the boundary outlines only (of all polygons touching also)
            bound_overlay = unary_union(self.gdf_polygons_partitioned.geometry.boundary)
            boundary_overlay = gpd.GeoSeries([bound_overlay])
            poly_list = list(polygonize(bound_overlay)) #Create polygons from it
            gdf_split = gpd.GeoDataFrame(geometry=poly_list) #And a dataframe
            gdf_split.set_crs(settings.CRS_GDA94, inplace=True)

            gdf_split2 = gpd.overlay(gdf_split, gdf_polygons_intersecting_single, how='intersection')
            # Perform the spatial join
            # This will find all geometries in gdf1 that intersect with gdf2
            # (i.e., touch at a point, line, or boundary)
            #gdf_common_boundary = gpd.sjoin(gdf_split, gdf_split.iloc[[2]], how='inner', predicate='intersects')
#            gdf_common_boundar = gpd.sjoin(gdf_split, gdf_single, how='inner', predicate='intersects')
            gdf_common_boundary = gpd.sjoin(self.gdf_polygons_partitioned, gdf_single, how='inner', predicate='intersects')
#            gdf_common_boundary = gpd.sjoin(gdf_split, self.gdf_polygons_partitioned, how='inner', predicate='within')

            # get the gdf_single split equivalent from gdf_common_boundary
#            base_polygon = self.get_base_polygon_gdf(gdf_single, gdf_common_boundary)
#            base_polygon = self.get_base_polygon_gdf(gdf_single, gdf_split)
            base_polygon = self.get_base_polygon_gdf(gdf_single, self.gdf_polygons_partitioned,)

            threshold = self.threshold if self.threshold else settings.SLIVER_AREALENGTH_THRESHOLD
            gdf_slivers = gdf_common_boundary[gdf_common_boundary.geometry.area/gdf_common_boundary.geometry.length < threshold]
            gdf_slivers_plus_base = gpd.GeoDataFrame(pd.concat([gdf_slivers, base_polygon], ignore_index=True))

            # all new historical polygons that intersect, excluding slivers and base polygon (gdf_single)
            #gdf_new_hist_polygons = gdf_common_boundary[~gdf_slivers_plus_base.geometry.contains(gdf_common_boundary.geometry)]
#            gdf_new_hist_polygons = gpd.overlay(gdf_common_boundary, gdf_slivers_plus_base, how='difference')
            gdf_new_hist_polygons = gpd.overlay(gdf_split, gdf_slivers_plus_base, how='difference')
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

            gdf_result = gpd.overlay(gdf_result, gdf_polygons_intersecting_single, how='intersection')
            #gdf_result['polygon_id'] = self.gdf_result.apply(get_base_polygon_id, args=(self.gdf_result, self.polygons), axis=1)
            gdf_result['polygon_src_id'] = gdf_result.apply(get_base_polygon_id, axis=1) # add column for the corresponding hist polygon_id
            gdf_result['polygon_src_id'] = gdf_result['polygon_src_id'].fillna(0).astype(int)
            import ipdb; ipdb.set_trace()

            #plot_overlay(gdf_five, polygons_intersecting_five)
            if 'index_right' in gdf_result.columns:
                gdf_result.drop('index_right', axis=1, inplace=True)

            # ['polygon_src_id', 'name', 'geom', 'version_id', 'proposal_id']
            gdf_result_filtered = gdf_result[['polygon_src_id', 'name', 'geometry']]
            gdf_result_filtered['version_id'] = self.next_version_id
            gdf_result_filtered['proposal_id'] = self.proposal_id

            # get un-partitioned parts from self.gdf_hist_polygons_total
            gdf_hist_polygons_net = gpd.overlay(self.gdf_hist_polygons_total, gdf_result, how='difference')
            gdf_hist_polygons_net = gdf_hist_polygons_net[gdf_hist_polygons_net.area>1] # drop tiny areas
            #self.save_global_intersecting_polygons(gdf_hist_polygons_net, 'silrec_polygonhistory')

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



import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union

def identify_slivers(gdf, base_polygon, buffer_distance=0.001, sliver_threshold=5):
    """
    Identify all touching polygon slivers for a given base polygon.

    Parameters:
    -----------
    gdf : GeoDataFrame
        Input GeoDataFrame containing multiple polygons
    base_polygon : shapely.geometry.Polygon
        The base polygon to find slivers for
    buffer_distance : float, default=0.001
        Buffer distance to find nearly touching polygons
    sliver_threshold : float, default=5
        Area/Length ratio threshold (slivers have ratio < threshold)

    Returns:
    --------
    GeoDataFrame containing the identified sliver polygons
    """

    # Create a copy to avoid modifying original
    import ipdb; ipdb.set_trace()
    working_gdf = gdf.copy()

    # Find polygons that touch or are within buffer distance of base_polygon
    buffered_base = base_polygon.buffer(buffer_distance)

    # Find potential slivers (excluding the base polygon itself)
#    potential_slivers = working_gdf[
#        (working_gdf.geometry.intersects(buffered_base)) &
#        (working_gdf.geometry != base_polygon)
#    ].copy()
    potential_slivers = gpd.overlay(working_gdf, base_polygon, how='difference')

    if len(potential_slivers) == 0:
        print("No potential slivers found near the base polygon")
        return gpd.GeoDataFrame(geometry=[], crs=gdf.crs)

    # Calculate area/length ratio for each potential sliver
    potential_slivers['area'] = potential_slivers.geometry.area
    potential_slivers['length'] = potential_slivers.geometry.length
    potential_slivers['area_length_ratio'] = potential_slivers['area'] / potential_slivers['length']

    # Identify slivers based on threshold
    slivers = potential_slivers[potential_slivers['area_length_ratio'] < sliver_threshold].copy()

    print(f"Found {len(slivers)} sliver polygons out of {len(potential_slivers)} potential candidates")

    # Add sliver information
    slivers['is_sliver'] = True
    slivers['sliver_ratio'] = slivers['area_length_ratio']

    return slivers[['geometry', 'is_sliver', 'sliver_ratio', 'area', 'length']]

def merge_slivers_into_base(gdf, base_polygon, slivers_gdf, buffer_distance=0.001):
    """
    Merge identified slivers into the base polygon and return updated GeoDataFrame.

    Parameters:
    -----------
    gdf : GeoDataFrame
        Original GeoDataFrame
    base_polygon : shapely.geometry.Polygon
        The base polygon to merge slivers into
    slivers_gdf : GeoDataFrame
        Slivers identified by identify_slivers function
    buffer_distance : float, default=0.001
        Buffer distance for robust merging

    Returns:
    --------
    GeoDataFrame with slivers merged into base polygon
    """

    if len(slivers_gdf) == 0:
        print("No slivers to merge")
        return gdf.copy()

    # Create a copy of the original GeoDataFrame
    updated_gdf = gdf.copy()

    # Get geometries to merge (base polygon + all slivers)
    geometries_to_merge = [base_polygon] + slivers_gdf.geometry.tolist()

    # Merge using unary_union with small buffer for robustness
    buffered_geometries = [geom.buffer(buffer_distance) for geom in geometries_to_merge]
    merged_geometry = unary_union(buffered_geometries)

    # Remove the buffer to get clean geometry
    final_merged_geometry = merged_geometry.buffer(-buffer_distance)

    # Ensure we have a valid polygon (handle potential MultiPolygon results)
    if final_merged_geometry.geom_type == 'MultiPolygon':
        # Take the largest polygon if it becomes a multipolygon
        polygons = list(final_merged_geometry.geoms)
        largest_polygon = max(polygons, key=lambda p: p.area)
        final_merged_geometry = largest_polygon
    elif final_merged_geometry.geom_type != 'Polygon':
        # If geometry type is unexpected, fall back to original base_polygon
        print(f"Warning: Unexpected geometry type after merging: {final_merged_geometry.geom_type}")
        final_merged_geometry = base_polygon

    # Update the base polygon in the GeoDataFrame
    base_polygon_mask = updated_gdf.geometry == base_polygon
    if base_polygon_mask.any():
        updated_gdf.loc[base_polygon_mask, 'geometry'] = final_merged_geometry
    else:
        # If base_polygon is not found by equality, find it by intersection
        base_idx = updated_gdf[updated_gdf.geometry.intersects(base_polygon)].index[0]
        updated_gdf.loc[base_idx, 'geometry'] = final_merged_geometry

    # Remove the sliver polygons from the GeoDataFrame
    sliver_indices = slivers_gdf.index
    updated_gdf = updated_gdf.drop(sliver_indices, errors='ignore')

    # Reset index
    updated_gdf = updated_gdf.reset_index(drop=True)

    print(f"Successfully merged {len(slivers_gdf)} slivers into base polygon")
    print(f"Updated GeoDataFrame has {len(updated_gdf)} polygons (original had {len(gdf)})")

    return updated_gdf
