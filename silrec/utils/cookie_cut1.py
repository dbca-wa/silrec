import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd

def create_intersection_polygons(gdf1, gdf2):
    """
    Intersect a single polygon from gdf1 with multiple polygons from gdf2
    and create new polygons at the intersecting boundaries.

    Parameters:
    -----------
    gdf1 : GeoDataFrame
        GeoDataFrame containing exactly one polygon geometry
    gdf2 : GeoDataFrame
        GeoDataFrame containing multiple polygon geometries

    Returns:
    --------
    GeoDataFrame
        New GeoDataFrame with intersection polygons and original attributes
    """

    # Validate input
    if len(gdf1) != 1:
        raise ValueError("gdf1 must contain exactly one polygon")

    if len(gdf2) == 0:
        raise ValueError("gdf2 must contain at least one polygon")

    # Get the single polygon from gdf1
    main_polygon = gdf1.geometry.iloc[0]

    # Perform intersection
    intersections = []

    for idx, row in gdf2.iterrows():
        poly2 = row.geometry

        # Check if geometries intersect
        if main_polygon.intersects(poly2):
            intersection = main_polygon.intersection(poly2)

            # Handle different geometry types that might result from intersection
            if intersection.is_empty:
                continue
            elif intersection.geom_type == 'Polygon':
                # Single polygon intersection
                new_row = row.copy()
                new_row['geometry'] = intersection
                intersections.append(new_row)
            elif intersection.geom_type == 'MultiPolygon':
                # Multiple polygons from intersection
                for poly in intersection.geoms:
                    new_row = row.copy()
                    new_row['geometry'] = poly
                    intersections.append(new_row)
            elif intersection.geom_type == 'GeometryCollection':
                # Filter only polygons from geometry collection
                for geom in intersection.geoms:
                    if geom.geom_type == 'Polygon':
                        new_row = row.copy()
                        new_row['geometry'] = geom
                        intersections.append(new_row)

    # Create result GeoDataFrame
    if intersections:
        result_gdf = gpd.GeoDataFrame(intersections, crs=gdf2.crs)

        # Add information about which gdf1 polygon was used (useful when extending function)
        result_gdf['source_gdf1_id'] = gdf1.index[0]

        return result_gdf
    else:
        # Return empty GeoDataFrame with same structure as gdf2
        return gpd.GeoDataFrame(columns=gdf2.columns.tolist() + ['source_gdf1_id'], crs=gdf2.crs)


# Alternative version using geopandas overlay (more efficient for larger datasets)
def create_intersection_polygons_overlay(gdf1, gdf2, how='intersection'):
    """
    Alternative implementation using geopandas overlay function.

    Parameters:
    -----------
    gdf1 : GeoDataFrame
        GeoDataFrame containing exactly one polygon geometry
    gdf2 : GeoDataFrame
        GeoDataFrame containing multiple polygon geometries
    how : str
        Overlay method: 'intersection', 'union', 'identity', etc.

    Returns:
    --------
    GeoDataFrame
        New GeoDataFrame with intersection polygons
    """

    if len(gdf1) != 1:
        raise ValueError("gdf1 must contain exactly one polygon")

    # Add identifier column to track original features
    gdf1_with_id = gdf1.copy()
    gdf2_with_id = gdf2.copy()
    gdf1_with_id['gdf1_id'] = gdf1.index[0]
    gdf2_with_id['gdf2_id'] = gdf2.index

    # Perform overlay operation
    result = gpd.overlay(gdf1_with_id, gdf2_with_id, how=how, keep_geom_type=True)

    return result


# Example usage:
if __name__ == "__main__":
    # Create sample data
    from shapely.geometry import Polygon

    # gdf1 with one polygon
    poly1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
    gdf1 = gpd.GeoDataFrame({'id': [1], 'name': ['main_polygon']},
                           geometry=[poly1], crs='EPSG:4326')

    # gdf2 with multiple polygons
    polygons2 = [
        Polygon([(1, 1), (4, 1), (4, 4), (1, 4)]),
        Polygon([(2, 0), (5, 0), (5, 2), (2, 2)]),
        Polygon([(0, 2), (2, 2), (2, 5), (0, 5)])
    ]
    gdf2 = gpd.GeoDataFrame({
        'id': [10, 20, 30],
        'type': ['A', 'B', 'C'],
        'value': [100, 200, 300]
    }, geometry=polygons2, crs='EPSG:4326')

    # Use the function
    result = create_intersection_polygons(gdf1, gdf2)
    print("Intersection result:")
    print(result)

    # Using overlay version
    result_overlay = create_intersection_polygons_overlay(gdf1, gdf2)
    print("\nOverlay result:")
    print(result_overlay)
