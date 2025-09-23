from django.conf import settings
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union, polygonize

def annotate_plot(gdf, ax, label_prefix=None):
    for idx, row in gdf.iterrows():
        # Get the centroid of the geometry for label placement
        # For points, this is the point itself. For polygons/lines, it's the centroid.
        # Use .representative_point() for polygons to ensure the point is within the polygon.
        if row.geometry.geom_type == 'Point':
            x, y = row.geometry.x, row.geometry.y
        else:
            x, y = row.geometry.centroid.x, row.geometry.centroid.y

        # Get the label text from a column in your GeoDataFrame (e.g., 'name_column')
        label = label_prefix + '_' + str(idx) if label_prefix else str(idx)

        # Add the label using annotate
        ax.annotate(text=label, xy=(x, y),
                    xytext=(3, 3), # Offset text slightly from the centroid
                    textcoords="offset points",
                    horizontalalignment='center',
                    fontsize=8,
                    color='black') # Customize color, font size, etc.
    return ax

def plot_gdf(gdf, annotate=True):
    ''' Annotate the plot with a feature index

        from silrec.utils.plot_utils import plot_gdf
        plot_gdf(gdf)
    '''
    def get_random_color():
        return "#%06x" % np.random.randint(0, 0xFFFFFF)

    # Create a list of random colors, one for each feature in the GeoDataFrame
    random_colors = [get_random_color() for _ in range(len(gdf))]
    gdf['random_color'] = random_colors

    # Assuming 'gdf' is your GeoDataFrame
    ax = gdf.plot(color=gdf['random_color'], figsize=(10, 10))

    # annotate the plot
    if annotate:
        annotate_plot(gdf, ax, label_prefix=None)

    plt.show()


def plot_overlay(gdf_base, gdf_hist, annotate=False):

    def get_random_color():
        return "#%06x" % np.random.randint(0, 0xFFFFFF)

    # Create a list of random colors, one for each feature in the GeoDataFrame
    random_colors = [get_random_color() for _ in range(len(gdf_base)+len(gdf_hist))]
    #gdf_overlay['random_color'] = random_colors


    # Create a plot to visualize the overlay
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # annotate the plot
    if annotate:
        annotate_plot(gdf_base, ax, label_prefix='base')
        annotate_plot(gdf_hist, ax, label_prefix='hist')

    # Plot the original GeoDataFrames with transparency
    gdf_base.plot(ax=ax, edgecolor='black', color='lightblue', alpha=0.5, label='Base Shapefile Geometries')
    gdf_hist.plot(ax=ax, edgecolor='red', color='lightgreen', alpha=0.5, label='Historical Intersecting Polygons')
    #gdf_base.plot(ax=ax, color=gdf['random_color'], edgecolor='black', alpha=0.5, label='Base Shapefile Geometries')
    #gdf_hist.plot(ax=ax, color=gdf['random_color'], edgecolor='red', alpha=0.5, label='Historical Intersecting Polygons')

    # Plot the overlay GeoDataFrame
    #overlay_gdf.plot(ax=ax, color='red', edgecolor='k', alpha=0.7, label='Intersection')

    # Add a legend and title
    ax.legend()
    ax.set_title('Overlay Plot of Base Shapefile Geometries and Hiostorical Intersecting Polygons')

    plt.show()

def get_base_polygon_gdf(gdf_base, gdf_common_boundary):
    ''' returns the equiv. of gdf_single, but the one after
        historical polygon intersection and subsequent splitting
        to form new polygons

        --> Returns the ''new split' base polygon
    '''
    centroids_gdf1 = gdf_base.geometry.centroid
    centroids_df = gpd.GeoDataFrame(geometry=centroids_gdf1)

    if 'index_right' in gdf_common_boundary.columns:
        gdf_common_boundary.drop(['index_right'], axis=1, inplace=True)

    return gpd.sjoin(gdf_common_boundary, centroids_df, how="inner", predicate="intersects")


def create_gdf():
    '''
    from silrec.utils.plot_utils import create_dummy_polygons, plot_gdf, plot_overlay, create_gdf
    polygons, gdf_single, polygons_intersecting_single, gdf_overlay, gdf_split, gdf_common_boundary, gdf_slivers, base_polygon, gdf_slivers_plus_base, gdf_new_hist_polygons, gdf_slivers_merged

    %matplotlib
    plot_gdf(gdf_slivers_merged)
    plot_gdf(gdf_new_hist_polygons)
    '''
    import geopandas as gpd
    from silrec.components.main.utils import polygons_to_gdf
    polygons = polygons_to_gdf()

    gdf_single = gpd.read_file('silrec/utils/Shapefiles/demarcation_single/demarcation_single_feature.shp')
    gdf_single.to_crs('EPSG:28350', inplace=True)

    gdf_five = gpd.read_file('silrec/utils/Shapefiles/demarcation_five/demarcation_five_features.shp')
    gdf_five.to_crs('EPSG:28350', inplace=True)

    # res = gdf_single.overlay(polygons, how='intersection')

    # Determine which geometries in polygons geodataframe intersect with any geometry in gdf_single
    # This creates a boolean Series
    intersects_mask_single = polygons.geometry.intersects(gdf_single.unary_union)
    intersects_mask_five   = polygons.geometry.intersects(gdf_five.unary_union)

    # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
    polygons_intersecting_single = polygons[intersects_mask_single]
    polygons_intersecting_five = polygons[intersects_mask_five]

    # plot the boundary outlines only (of all polygons touching also)
    bound_single = unary_union(polygons_intersecting_single.geometry.boundary)
    boundary_single = gpd.GeoSeries([bound_single])
    #boundary_single.plot()

    # non overlapping overlayed geometries (creates independent partitioned geometries)
    gdf_overlay = gpd.overlay(gdf_single, polygons_intersecting_single, how='union')

    # plot the boundary outlines only (of all polygons touching also)
    bound_overlay = unary_union(gdf_overlay.geometry.boundary)
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
    gdf_common_boundary = gpd.sjoin(gdf_split, gdf_single, how='inner', predicate='intersects')

    # get the gdf_single split equivalent from gdf_common_boundary
    base_polygon = get_base_polygon_gdf(gdf_single, gdf_common_boundary)

    threshold = 5
    gdf_slivers = gdf_common_boundary[gdf_common_boundary.geometry.area/gdf_common_boundary.geometry.length < threshold]
    gdf_slivers_plus_base = gpd.GeoDataFrame(pd.concat([gdf_slivers, base_polygon], ignore_index=True))


    # all new historical polygons that intersect, excluding slivers and base polygon (gdf_single)
    #gdf_new_hist_polygons = gdf_common_boundary[~gdf_slivers_plus_base.geometry.contains(gdf_common_boundary.geometry)]
    gdf_new_hist_polygons = gpd.overlay(gdf_common_boundary, gdf_slivers_plus_base, how='difference')

    # View the plots - the sum of the two below make-up 'gdf_common_boundary'
    # plot_gdf(gdf_new_hist_polygons) # Everything excluding slivers + base_polygon
    # plot_gdf(gdf_slivers_plus_base) # Only slivers + base_polygon

    gdf_slivers_merged = gdf_slivers_plus_base.dissolve() # Multipolygon
    #gdf_slivers_merged = gdf_slivers_plus_base.dissolve().explode()) # Polygon(s) - >1 if there gaps between polygons preventing merge to a single polygon

    #plot_overlay(gdf_five, polygons_intersecting_five)
    return polygons, gdf_single, polygons_intersecting_single, gdf_overlay, gdf_split, gdf_common_boundary, gdf_slivers,base_polygon, gdf_slivers_plus_base, gdf_new_hist_polygons, gdf_slivers_merged


def create_dummy_polygons():
    '''
    poly, polys3, df, df3, df_intersecting, gdf_overlay = create_dummy_polygons()
    '''
    import matplotlib.pyplot as plt
    import numpy as np
    import geopandas as gpd
    import pandas as pd
    from silrec.utils.plot_utils import annotate_plot, plot_gdf, plot_overlay, create_gdf
    poly = gpd.GeoSeries([Polygon([(1,1), (4,1), (4,4), (1,4)])])
    polys3 = gpd.GeoSeries([Polygon([(0,0), (2,0), (2,2), (0,2)]),Polygon([(1,1), (4,1), (4,4), (1,4)]),Polygon([(3,3), (5,3), (5,5), (3,5)])])
    df = gpd.GeoDataFrame({'geometry': poly, 'df':[0]})
    df3 = gpd.GeoDataFrame({'geometry': polys3, 'df3':[1,2,3]})
    intersects_mask = df3.geometry.intersects(df.unary_union)
    df_intersecting = df3[intersects_mask]
    gdf_overlay = gpd.overlay(df, df_intersecting, how='union')
    #plot_overlay(df3, df)
    return poly, polys3, df, df3, df_intersecting, gdf_overlay


def merge_base_polygon_to_slivers(gdf_base, gdf_slivers, threshold=10):
    combined_gdf = gpd.GeoDataFrame(pd.concat([gdf_base, gdf_slivers], ignore_index=True))
    return combined_gdf.dissolve()
    base_boundary = gpd.GeoDataFrame(pd.concat([base_polygon, gdf_slivers], ignore_index=True)).boundary.iloc[[0]]

    In [290]: base_boundary.convex_hull



def merge_slivers(gdf_base, gdf_common_boundary, threshold=10):
    ''' Returns a single polygon with slivers below a given threshold Area/Length ratio merged into the base_gdf

        gdf_base --> Polygon from user input Shapefile
        gdf_common_boundary - gdf from touching slivers (touching gdf_base) created from intersecting historical polygons

        threshold --> Area/Length (m), used to decide which slivers to mege into gdf_base

        returns --> a single polygon with slivers below a given threshold Area/Length ratio
    '''
    area_length_ratio = gdf_common_boundary.area / gdf_common_boundary.length
    gdf_slivers = gdf_common_boundary[area_length_ratio < threshold]

    combined_gdf = gpd.GeoDataFrame(pd.concat([gdf_base, gdf_slivers], ignore_index=True))

    return combined_gdf.dissolve()

if __name__ == '__main__':
    poly, polys3, df, df3, df_intersecting, gdf_overlay = create_dummy_polygons()

