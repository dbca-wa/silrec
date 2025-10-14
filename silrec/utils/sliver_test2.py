import geopandas as gpd
from shapely.geometry import Polygon

def find_largest_neighbor(gdf1, gdf2):
    """
    Find the neighboring/touching polygon in gdf2 with the largest area

    Parameters:
    gdf1: GeoDataFrame with a single polygon/multipolygon
    gdf2: GeoDataFrame with polygons to check for neighbors

    Returns:
    GeoDataFrame containing the largest neighbor or empty GeoDataFrame if no neighbors found
    """
    # Get the single geometry from gdf1
    if len(gdf1) != 1:
        raise ValueError("gdf1 must contain exactly one geometry")

    target_geom = gdf1.geometry.iloc[0]

    # Find all polygons in gdf2 that touch/intersect with the target geometry
    neighbors_mask = gdf2.geometry.touches(target_geom) | gdf2.geometry.intersects(target_geom)

    # Exclude the case where a polygon intersects with itself (if gdf1 and gdf2 overlap)
    neighbors = gdf2[neighbors_mask].copy()

    # If no neighbors found, return empty GeoDataFrame
    if len(neighbors) == 0:
        return gpd.GeoDataFrame(columns=gdf2.columns, crs=gdf2.crs)

    # Calculate areas for all neighbors
    neighbors['area'] = neighbors.geometry.area

    # Find the neighbor with the largest area and return as single-row GeoDataFrame
    largest_idx = neighbors['area'].idxmax()
    largest_neighbor_gdf = neighbors.loc[[largest_idx]]  # Note double brackets to keep as DataFrame

    return largest_neighbor_gdf

# Alternative more explicit version with additional options
def find_largest_neighbor_advanced(gdf1, gdf2, method='touches'):
    """
    Advanced version with different neighbor detection methods

    Parameters:
    gdf1: GeoDataFrame with a single polygon/multipolygon
    gdf2: GeoDataFrame with polygons to check for neighbors
    method: 'touches' (only boundary contact), 'intersects' (any overlap),
            'buffer' (within buffer distance)

    Returns:
    Tuple (largest_neighbor_gdf, all_neighbors_gdf)
    """
    if len(gdf1) != 1:
        raise ValueError("gdf1 must contain exactly one geometry")

    target_geom = gdf1.geometry.iloc[0]

    if method == 'touches':
        # Only polygons that share a boundary (touch but don't overlap interiors)
        neighbors_mask = gdf2.geometry.touches(target_geom)
    elif method == 'intersects':
        # Any spatial interaction including overlap and touching
        neighbors_mask = gdf2.geometry.intersects(target_geom)
    elif method == 'buffer':
        # Neighbors within a small buffer distance (adjust buffer distance as needed)
        buffer_distance = 0.001  # Adjust based on your CRS units
        buffered = target_geom.buffer(buffer_distance)
        neighbors_mask = gdf2.geometry.intersects(buffered)
        # Exclude self-intersection
        neighbors_mask = neighbors_mask & ~gdf2.geometry.touches(target_geom)
    else:
        raise ValueError("Method must be 'touches', 'intersects', or 'buffer'")

    neighbors = gdf2[neighbors_mask].copy()

    if len(neighbors) == 0:
        return gpd.GeoDataFrame(columns=gdf2.columns, crs=gdf2.crs), neighbors

    # Calculate areas and find largest
    neighbors['area'] = neighbors.geometry.area
    largest_idx = neighbors['area'].idxmax()
    largest_neighbor_gdf = neighbors.loc[[largest_idx]]  # Double brackets for DataFrame

    return largest_neighbor_gdf, neighbors

# Optimized version with spatial index for better performance
def find_largest_neighbor_spatial_index(gdf1, gdf2):
    """
    Version using spatial index for better performance with large datasets
    """
    if len(gdf1) != 1:
        raise ValueError("gdf1 must contain exactly one geometry")

    target_geom = gdf1.geometry.iloc[0]

    # Use spatial index to find potential candidates first
    spatial_index = gdf2.sindex
    possible_matches_index = list(spatial_index.intersection(target_geom.bounds))
    possible_matches = gdf2.iloc[possible_matches_index]

    # Then precise check on the subset
    precise_matches = possible_matches[
        possible_matches.geometry.touches(target_geom) |
        possible_matches.geometry.intersects(target_geom)
    ].copy()

    if len(precise_matches) == 0:
        return gpd.GeoDataFrame(columns=gdf2.columns, crs=gdf2.crs)

    # Calculate areas and find largest
    precise_matches['area'] = precise_matches.geometry.area
    largest_idx = precise_matches['area'].idxmax()
    largest_neighbor_gdf = precise_matches.loc[[largest_idx]]

    return largest_neighbor_gdf

# Example usage:
if __name__ == "__main__":
    # Create example data
    from shapely.geometry import Polygon

    # gdf1 with single polygon
    poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    gdf1 = gpd.GeoDataFrame({'id': [1]}, geometry=[poly1], crs="EPSG:4326")

    # gdf2 with multiple polygons
    polygons = [
        Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),  # Touching neighbor (area = 1)
        Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),  # Touching neighbor (area = 1)
        Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),  # Touching neighbor (area = 1)
        Polygon([(2, 0), (3, 0), (3, 3), (2, 3)]),  # Larger touching neighbor (area = 3)
        Polygon([(5, 5), (6, 5), (6, 6), (5, 6)])   # Non-touching polygon
    ]
    gdf2 = gpd.GeoDataFrame({'id': [1, 2, 3, 4, 5]}, geometry=polygons, crs="EPSG:4326")

    # Find largest neighbor
    largest_neighbor_gdf = find_largest_neighbor(gdf1, gdf2)

    if not largest_neighbor_gdf.empty:
        print(f"Largest neighbor found:")
        print(largest_neighbor_gdf)
        print(f"\nLargest neighbor ID: {largest_neighbor_gdf['id'].iloc[0]}")
        print(f"Largest neighbor area: {largest_neighbor_gdf['area'].iloc[0]}")
    else:
        print("No neighbors found")

    # Using the advanced version
    print("\nUsing advanced version:")
    largest_gdf, all_neighbors = find_largest_neighbor_advanced(gdf1, gdf2)
    if not largest_gdf.empty:
        print(f"All neighbors found: {len(all_neighbors)}")
        print(f"Largest neighbor area: {largest_gdf['area'].iloc[0]}")
