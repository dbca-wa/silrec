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
    tuple (GeoDataFrame, GeoDataFrame)
        result_gdf: New GeoDataFrame with intersection polygons
        gdf2_excl_result_gdf: gdf2 excluding the intersection polygons
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
    intersecting_indices = set()  # Track which gdf2 polygons intersected

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
                intersecting_indices.add(idx)
            elif intersection.geom_type == 'MultiPolygon':
                # Multiple polygons from intersection
                for poly in intersection.geoms:
                    new_row = row.copy()
                    new_row['geometry'] = poly
                    intersections.append(new_row)
                intersecting_indices.add(idx)
            elif intersection.geom_type == 'GeometryCollection':
                # Filter only polygons from geometry collection
                polygons_found = False
                for geom in intersection.geoms:
                    if geom.geom_type == 'Polygon':
                        new_row = row.copy()
                        new_row['geometry'] = geom
                        intersections.append(new_row)
                        polygons_found = True
                if polygons_found:
                    intersecting_indices.add(idx)

    # Create result GeoDataFrame
    if intersections:
        result_gdf = gpd.GeoDataFrame(intersections, crs=gdf2.crs)

        # Add information about which gdf1 polygon was used
        result_gdf['source_gdf1_id'] = gdf1.index[0]

        # Create gdf2 excluding intersection polygons
        gdf2_excl_result = gdf2[~gdf2.index.isin(intersecting_indices)].copy()

        return result_gdf, gdf2_excl_result
    else:
        # Return empty GeoDataFrame for intersections and original gdf2
        empty_gdf = gpd.GeoDataFrame(columns=gdf2.columns.tolist() + ['source_gdf1_id'], crs=gdf2.crs)
        return empty_gdf, gdf2.copy()


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
    tuple (GeoDataFrame, GeoDataFrame)
        result_gdf: New GeoDataFrame with intersection polygons
        gdf2_excl_result_gdf: gdf2 excluding the intersection polygons
    """

    if len(gdf1) != 1:
        raise ValueError("gdf1 must contain exactly one polygon")

    # Add identifier columns to track original features
    gdf1_with_id = gdf1.copy()
    gdf2_with_id = gdf2.copy()
    gdf1_with_id['gdf1_id'] = gdf1.index[0]
    gdf2_with_id['gdf2_id'] = gdf2.index

    # Perform overlay operation
    result = gpd.overlay(gdf1_with_id, gdf2_with_id, how=how, keep_geom_type=True)

    # Get indices of gdf2 polygons that were used in intersections
    if not result.empty and 'gdf2_id' in result.columns:
        intersecting_indices = result['gdf2_id'].unique()
        gdf2_excl_result = gdf2[~gdf2.index.isin(intersecting_indices)].copy()
    else:
        gdf2_excl_result = gdf2.copy()

    return result, gdf2_excl_result


# More sophisticated version that handles the difference operation properly
def create_intersection_polygons_with_difference(gdf1, gdf2):
    """
    Enhanced version that properly computes the difference for non-intersecting parts.

    Parameters:
    -----------
    gdf1 : GeoDataFrame
        GeoDataFrame containing exactly one polygon geometry
    gdf2 : GeoDataFrame
        GeoDataFrame containing multiple polygon geometries

    Returns:
    --------
    tuple (GeoDataFrame, GeoDataFrame)
        result_gdf: New GeoDataFrame with intersection polygons
        gdf2_excl_result_gdf: gdf2 with polygons updated to exclude intersections
    """

    # Validate input
    if len(gdf1) != 1:
        raise ValueError("gdf1 must contain exactly one polygon")

    if len(gdf2) == 0:
        raise ValueError("gdf2 must contain at least one polygon")

    # Get the single polygon from gdf1
    main_polygon = gdf1.geometry.iloc[0]

    intersections = []
    updated_gdf2_rows = []

    for idx, row in gdf2.iterrows():
        poly2 = row.geometry

        # Check if geometries intersect
        if main_polygon.intersects(poly2):
            intersection = main_polygon.intersection(poly2)
            difference = poly2.difference(main_polygon)

            # Handle intersection
            if not intersection.is_empty:
                if intersection.geom_type == 'Polygon':
                    new_row = row.copy()
                    new_row['geometry'] = intersection
                    intersections.append(new_row)
                elif intersection.geom_type == 'MultiPolygon':
                    for poly in intersection.geoms:
                        new_row = row.copy()
                        new_row['geometry'] = poly
                        intersections.append(new_row)
                elif intersection.geom_type == 'GeometryCollection':
                    for geom in intersection.geoms:
                        if geom.geom_type == 'Polygon':
                            new_row = row.copy()
                            new_row['geometry'] = geom
                            intersections.append(new_row)

            # Handle difference (non-intersecting part)
            if not difference.is_empty:
                if difference.geom_type in ['Polygon', 'MultiPolygon']:
                    updated_row = row.copy()
                    updated_row['geometry'] = difference
                    updated_gdf2_rows.append(updated_row)
        else:
            # No intersection, keep original polygon
            updated_gdf2_rows.append(row.copy())

    # Create result GeoDataFrame
    if intersections:
        result_gdf = gpd.GeoDataFrame(intersections, crs=gdf2.crs)
        result_gdf['source_gdf1_id'] = gdf1.index[0]
    else:
        result_gdf = gpd.GeoDataFrame(columns=gdf2.columns.tolist() + ['source_gdf1_id'], crs=gdf2.crs)

    # Create updated gdf2 excluding intersection areas
    if updated_gdf2_rows:
        gdf2_excl_result = gpd.GeoDataFrame(updated_gdf2_rows, crs=gdf2.crs)
    else:
        gdf2_excl_result = gpd.GeoDataFrame(columns=gdf2.columns, crs=gdf2.crs)

    return result_gdf, gdf2_excl_result


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
        Polygon([(1, 1), (4, 1), (4, 4), (1, 4)]),  # Will intersect
        Polygon([(2, 0), (5, 0), (5, 2), (2, 2)]),  # Will intersect
        Polygon([(0, 2), (2, 2), (2, 5), (0, 5)]),  # Will intersect
        Polygon([(4, 4), (6, 4), (6, 6), (4, 6)])   # Will NOT intersect
    ]
    gdf2 = gpd.GeoDataFrame({
        'id': [10, 20, 30, 40],
        'type': ['A', 'B', 'C', 'D'],
        'value': [100, 200, 300, 400]
    }, geometry=polygons2, crs='EPSG:4326')

    print("Original gdf2 has", len(gdf2), "polygons")

    # Use the function
    result_gdf, gdf2_excl = create_intersection_polygons(gdf1, gdf2)
    print("\nIntersection result has", len(result_gdf), "polygons")
    print("gdf2 excluding intersections has", len(gdf2_excl), "polygons")

    # Using the enhanced version with proper difference
    result_gdf2, gdf2_excl2 = create_intersection_polygons_with_difference(gdf1, gdf2)
    print("\nEnhanced version:")
    print("Intersection result has", len(result_gdf2), "polygons")
    print("gdf2 excluding intersections has", len(gdf2_excl2), "polygons")

    # Verify that no overlapping geometries exist between results
    print("\nVerification:")
    print("Total original gdf2 polygons:", len(gdf2))
    print("Intersection polygons + remaining polygons:", len(result_gdf2) + len(gdf2_excl2))
