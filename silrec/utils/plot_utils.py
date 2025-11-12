from django.conf import settings
from sqlalchemy import create_engine
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union, polygonize

def annotate_plot(gdf, ax, user_defined_label=None, label_prefix=None):
    row_idx = 0
    for idx, row in gdf.iterrows():
        # Get the centroid of the geometry for label placement
        # For points, this is the point itself. For polygons/lines, it's the centroid.
        # Use .representative_point() for polygons to ensure the point is within the polygon.

        #idx = row.name
        label_prefix = None
        row_geom = row.geometry if 'geometry' in gdf.columns else row.geom
        if row_geom.geom_type == 'Point':
            x, y = row_geom.x, row_geom.y
        else:
            #x, y = row_geom.centroid.x, row_geom.centroid.y
            x, y = row_geom.representative_point().x, row_geom.representative_point().y

        # Get the label text from a column in your GeoDataFrame (e.g., 'name_column')
        if 'origin' in row.keys().to_list() and row.origin == 'BASE':
            label_prefix = 'BASE'

        label = str(idx)
        if label_prefix:
            label = f'{label_prefix} ({idx})'
        else:
            if user_defined_label:
                if user_defined_label in gdf.columns:
                    label = row[user_defined_label]

        # Add the label using annotate
        ax.annotate(text=label, xy=(x, y),
                    xytext=(3, 3), # Offset text slightly from the centroid
                    textcoords="offset points",
                    horizontalalignment='center',
                    fontsize=9,
                    color='black') # Customize color, font size, etc.
        row_idx += 1
    return ax

def plot_gdf(gdf, annotate=True, user_defined_label=None):
    ''' Annotate the plot with a feature index

        from silrec.utils.plot_utils import plot_gdf
        plot_gdf(gdf)

        plot_gdf(gdf_result)
        plot_gdf(gdf_result, user_defined_label='polygon_id')
    '''
    def get_random_color():
        # Generate colors where at least one component is bright
        r = np.random.randint(128, 256)  # 128-255
        g = np.random.randint(128, 256)  # 128-255
        b = np.random.randint(128, 256)  # 128-255
        return f"#{r:02x}{g:02x}{b:02x}"


    # Create a list of random colors, one for each feature in the GeoDataFrame
    random_colors = [get_random_color() for _ in range(len(gdf))]
    gdf['random_color'] = random_colors

    # Assuming 'gdf' is your GeoDataFrame
    ax = gdf.plot(color=gdf['random_color'], figsize=(10, 10))

    npolys = len(gdf)
    area_ha = round(gdf.area.sum()/10000, 2)
    ax.set_title(f'Polys {npolys}. Area Ha {area_ha}')

    # annotate the plot
    if annotate:
        annotate_plot(gdf, ax, user_defined_label, label_prefix=None)

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

def plot_multi(gdf_list, use_random_cols=True, user_defined_label=None):
    '''
    plot_multi([gdf_hist, gdf_result, gdf_result])
    plot_multi([gdf_hist, gdf_result, gdf_result], user_defined_label=['polygon_id', 'polygon_id', 'poly_id_new'])
    '''

    def get_random_color():
        # Generate colors where at least one component is bright
        r = np.random.randint(128, 256)  # 128-255
        g = np.random.randint(128, 256)  # 128-255
        b = np.random.randint(128, 256)  # 128-255
        return f"#{r:02x}{g:02x}{b:02x}"

    user_label = None
    if len(gdf_list)<=3:
        nrows = 1
    elif len(gdf_list)>3 and len(gdf_list)<=6:
        nrows = 2
    else:
        raise Exception(f'Max. number of gdfs is 6: {len(gdf_list)}')

    if len(gdf_list)==1:
        ncols = 1
    elif len(gdf_list)==2:
        ncols = 2
    else:
        ncols = 3


    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15, 10))
    for i, gdf in enumerate(gdf_list):

#        random_colors = [get_random_color() for _ in range(len(gdf))]
        if use_random_cols is True or 'origin' not in list(gdf.columns):
            random_colors = [get_random_color() for _ in range(len(gdf))]
        else:
            random_colors = ['cornflowerblue' for _ in range(len(gdf))]
            try:
                # colour the base_polygon
                indices = gdf.index[gdf['origin'] == 'BASE'].tolist()
                idx = gdf.index.get_loc(indices[0])
                random_colors[idx] = 'limegreen'

                # colour the neighbouring polygons that have been cookie-cut
                indices_cut = gdf.index[gdf['origin'] == 'CUT'].tolist()
                if len(indices_cut) > 0:
                    for idx_cut in indices_cut:
                        idx = gdf.index.get_loc(idx_cut)
                        random_colors[idx] = 'cyan'

            except Exception as e:
                print(f'{e}')

        npolys = len(gdf)
        area_ha = round(gdf.area.sum()/10000, 2)
        if nrows==1:
            if user_defined_label:
                user_label = user_defined_label[i] if type(user_defined_label)==list else user_defined_label
            col = i % 3   # Calculate column index
            #gdf.plot(ax=axs[col], color='blue', edgecolor='black')
            #gdf.plot(ax=axs[col], color=random_colors[:npolys+1], edgecolor='black')
            gdf.plot(ax=axs[col], color=random_colors, edgecolor='black')
            #gdf.plot(ax=axs[col], color='blue', edgecolor='black')
            axs[col].set_title(f'Polys {npolys}. Area Ha {area_ha}')
            annotate_plot(gdf, axs[col], user_label, label_prefix=None)
        else:
            if user_defined_label:
                user_label = user_defined_label[i] if type(user_defined_label)==list else user_defined_label
            row = i // 3  # Calculate row index
            col = i % 3   # Calculate column index
            #gdf.plot(ax=axs[row, col], color=random_colors[:npolys+1], edgecolor='black', linewidth=0.5)
            gdf.plot(ax=axs[row, col], color=random_colors, edgecolor='black', linewidth=0.5)
            #gdf.plot(ax=axs[row, col], color='blue', edgecolor='black', linewidth=0.5)
            axs[row,col].set_title(f'Polys {npolys}. Area Ha {area_ha}')
            annotate_plot(gdf, axs[row,col], user_label, label_prefix=None)

    # Handle extra subplots if number of GDFs is less than 6
    if len(gdf_list) > 3 and len(gdf_list) < 6:
        for j in range(len(gdf_list), 6):
            row = j // 3
            col = j % 3
            axs[row, col].set_visible(False) # Hide empty subplots

    # Display the plot
    plt.tight_layout() # Adjusts subplot params for a tight layout
    #plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent title overlap
    plt.show()

def plot_multi_test():
    gdf_list = [
        gpd.GeoDataFrame({'col1': [1, 2], 'geometry': [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326"),
        gpd.GeoDataFrame({'col2': [3, 4], 'geometry': [Point(2, 2), Point(3, 3)]}, crs="EPSG:4326"),
        gpd.GeoDataFrame({'col3': [5, 6], 'geometry': [Point(4, 4), Point(5, 5)]}, crs="EPSG:4326"),

        gpd.GeoDataFrame({'col1': [1, 2], 'geometry': [Point(0, 0), Point(1, 1)]}, crs="EPSG:4326"),
        gpd.GeoDataFrame({'col2': [3, 4], 'geometry': [Point(2, 2), Point(3, 3)]}, crs="EPSG:4326"),
        gpd.GeoDataFrame({'col3': [5, 6], 'geometry': [Point(4, 4), Point(5, 5)]}, crs="EPSG:4326"),
    ]

    if len(gdf_list)<=3:
        nrows = 1
    elif len(gdf_list)>3 and len(gdf_list)<=6:
        nrows = 2
    else:
        raise Exception(f'Max. number of gdfs is 6: {len(gdf_list)}')

    if len(gdf_list)==1:
        ncols = 1
    elif len(gdf_list)==2:
        ncols = 2
    else:
        ncols = 3

    #import ipdb; ipdb.set_trace()
    fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(15, 10))
    for i, gdf in enumerate(gdf_list):
        if nrows==1:
            col = i % 3   # Calculate column index
            gdf.plot(ax=axs[col], color='blue', edgecolor='black')
        else:
            row = i // 3  # Calculate row index
            col = i % 3   # Calculate column index
            gdf.plot(ax=axs[row, col], edgecolor='black', linewidth=0.5)

    # Handle extra subplots if number of GDFs is less than 6
    if len(gdf_list) > 3 and len(gdf_list) < 6:
        for j in range(len(gdf_list), 6):
            row = j // 3
            col = j % 3
            axs[row, col].set_visible(False) # Hide empty subplots

    # Display the plot
    plt.tight_layout() # Adjusts subplot params for a tight layout
    #plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent title overlap
    plt.show()

def get_conn_engine():
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

def get_base_polygon_id(row, polygons):
    ''' for given split polygon, returns the polygon_id of the parent (historical polygons gdf) polygon

        --> Returns the parent polygon_id (intersected by the centroid)

        usage: gdf_tmp['polygon_id'] = gdf_tmp.apply(get_base_polygon_id, axis=1)
    '''
    # Convert Centroid POINT to GDF
    centroid_point = row.geometry.centroid
    data = {'geometry': [centroid_point]}
    centroid_gdf = gpd.GeoDataFrame(data, geometry='geometry', crs=settings.CRS_GDA94)

    if 'index_right' in polygons.columns:
        polygons.drop(['index_right'], axis=1, inplace=True)

    gdf = gpd.sjoin(polygons, centroid_gdf, how="inner", predicate="intersects")
    return None if gdf.empty else gdf.polygon_id.iloc[0]


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
    polygons, gdf_single, polygons_intersecting_single, gdf_overlay, gdf_split, gdf_common_boundary, gdf_slivers, base_polygon, gdf_slivers_plus_base, gdf_new_hist_polygons, gdf_slivers_merged, gdf_result

    %matplotlib
    plot_gdf(gdf_slivers_merged)
    plot_gdf(gdf_new_hist_polygons)
    '''
    import geopandas as gpd
    from silrec.components.main.utils import polygons_to_gdf
    #polygons = polygons_to_gdf()

    sql='select * from polygon;'
    polygons = gpd.read_postgis(sql, con=get_conn_engine(), geom_col='geom')

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
    #import ipdb; ipdb.set_trace()
    gdf_result = gpd.GeoDataFrame(pd.concat([gdf_slivers_merged, gdf_new_hist_polygons], ignore_index=True))
    #gdf_result['polygon_id'] = gdf_result.apply(get_base_polygon_id, args=(gdf_result, polygons), axis=1)

    #plot_overlay(gdf_five, polygons_intersecting_five)
    return polygons, gdf_single, polygons_intersecting_single, gdf_overlay, gdf_split, gdf_common_boundary, \
           gdf_slivers,base_polygon, gdf_slivers_plus_base, gdf_new_hist_polygons, gdf_slivers_merged, gdf_result


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

