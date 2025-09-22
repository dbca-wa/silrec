import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

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
    gdf_overlay['random_color'] = random_colors


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

def create_gdf():
    import geopandas as gpd
    from silrec.components.main.utils import polygons_to_gdf
    polygons = polygons_to_gdf()

    gdf_single = gpd.read_file('/home/jawaidm/Shapefiles/demarcation_single/demarcation_single_feature.shp')
    gdf_single.to_crs('EPSG:28350', inplace=True)

    gdf_five = gpd.read_file('/home/jawaidm/Shapefiles/demarcation_five/demarcation_five_features.shp')
    gdf_five.to_crs('EPSG:28350', inplace=True)

    # res = gdf_single.overlay(polygons, how='intersection')

    # Determine which geometries in polygons geodataframe intersect with any geometry in gdf_single
    # This creates a boolean Series
    intersects_mask_single = polygons.geometry.intersects(gdf_single.unary_union)
    intersects_mask_five   = polygons.geometry.intersects(gdf_five.unary_union)

    # polygons_intersecting are a subset of geometries for gdf polygons that intersect/overlay the base gdf (gdf_single)
    polygons_intersecting_single = polygons[intersects_mask_single]
    polygons_intersecting_five = polygons[intersects_mask_five]

    # non overlapping overlayed germs (creates independent slivers)
    gdf_overlay = gpd.overlay(gdf_single, polygons_intersecting_single, how='union')

    gdf1 = gdf_overlay.iloc[[7]]
    gdf2 = gdf_overlay.iloc[[2,3]]
    # Find geometries in gdf2 that have a common boundary (touch) with gdf1
    common_boundary_geos = gpd.sjoin(gdf2, gdf1, how='inner', predicate='touches')

    #plot_overlay(gdf_five, polygons_intersecting_five)
    return polygons, gdf_single, gdf_five, polygons_intersecting_single, polygons_intersecting_five, gdf_overlay



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

