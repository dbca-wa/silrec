import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from itertools import combinations

def find_touching_polygons(gdf):
    """
    Find all pairs of touching polygons by their index.

    from silrec.utils.sliver_merge_utils1 import find_touching_polygons, merge_polygons
    find_touching_polygons(gdf)

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame with polygon geometries

    Returns:
    --------
    list of tuples
        List of (index1, index2) pairs where polygons touch
    """
    touching_pairs = []

    # Create spatial index for faster querying
    spatial_index = gdf.sindex

    for idx1, geom1 in gdf.geometry.items():
        # Find potential candidates using spatial index
        possible_matches_idx = list(spatial_index.intersection(geom1.bounds))
        possible_matches = gdf.iloc[possible_matches_idx]

        for idx2, geom2 in possible_matches.geometry.items():
            # Skip self-comparison and duplicate pairs
            if idx1 >= idx2:
                continue

            # Check if polygons touch (share boundary but interiors don't intersect)
            if geom1.touches(geom2):
                touching_pairs.append((idx1, idx2))

    return touching_pairs

def merge_polygons(gdf, polygon_ids, validate_touching=True):
    """
    Merge/dissolve polygons by their indices, ensuring net area is preserved.

    from silrec.utils.sliver_merge_utils1 import find_touching_polygons, merge_polygons
    plot_gdf(merge_polygons(gdf, [42,41, 34,29, 6]))

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Input GeoDataFrame with polygon geometries
    polygon_ids : list
        List of polygon indices to merge
    validate_touching : bool, default True
        Whether to validate that all polygons touch each other

    Returns:
    --------
    geopandas.GeoDataFrame
        New GeoDataFrame with merged polygon and preserved attributes

    Raises:
    -------
    ValueError: If polygons don't touch when validate_touching=True
    """
    if len(polygon_ids) < 2:
        raise ValueError("At least 2 polygon IDs required for merging")

    # Filter the polygons to merge
    polygons_to_merge = gdf.loc[polygon_ids]

    if validate_touching:
        # Check if all polygons form a connected touching group
        if not _are_polygons_connected(polygons_to_merge):
            raise ValueError("Not all provided polygons touch each other directly or indirectly")

    # Calculate total area before merging (for validation)
    total_area_before = polygons_to_merge.geometry.area.sum()

    # Create a mask for polygons to keep vs merge
    merge_mask = gdf.index.isin(polygon_ids)

    # Separate polygons that will be merged from those that will remain
    polygons_remaining = gdf[~merge_mask].copy()

    # Merge the selected polygons
    merged_geometry = polygons_to_merge.geometry.unary_union

    # Handle case where unary_union returns MultiPolygon vs Polygon
    if merged_geometry.geom_type == 'MultiPolygon':
        # For MultiPolygon, we might want to keep it or convert to single Polygon
        # Here we'll keep it as is, but you could add logic to handle this differently
        final_geometry = merged_geometry
    else:
        final_geometry = merged_geometry

    # Calculate area after merging
    total_area_after = final_geometry.area

    # Validate area preservation (allowing for small floating point differences)
    area_tolerance = 1e-6
    if abs(total_area_before - total_area_after) > area_tolerance:
        raise ValueError(f"Area not preserved during merge. Before: {total_area_before}, After: {total_area_after}")

    # Create new row for merged polygon
    # For attributes, you might want to implement custom logic based on your needs
    # Here we'll take the first polygon's attributes as an example
    merged_attributes = polygons_to_merge.iloc[0].drop('geometry').to_dict()

    # Create new GeoDataFrame for the merged result
    merged_gdf = gpd.GeoDataFrame(
        [merged_attributes],
        geometry=[final_geometry],
        crs=gdf.crs
    )

    # Combine with remaining polygons
    result_gdf = pd.concat([polygons_remaining, merged_gdf], ignore_index=True)

    return result_gdf

def _are_polygons_connected(gdf):
    """
    Helper function to check if all polygons in a GeoDataFrame form a connected graph
    where each polygon touches at least one other polygon in the set.
    """
    if len(gdf) == 1:
        return True

    # Build adjacency graph
    graph = {idx: set() for idx in gdf.index}
    spatial_index = gdf.sindex

    for idx1, geom1 in gdf.geometry.items():
        possible_matches_idx = list(spatial_index.intersection(geom1.bounds))
        possible_matches = gdf.iloc[possible_matches_idx]

        for idx2, geom2 in possible_matches.geometry.items():
            if idx1 != idx2 and geom1.touches(geom2):
                graph[idx1].add(idx2)
                graph[idx2].add(idx1)

    # Check connectivity using BFS
    visited = set()
    queue = [next(iter(gdf.index))]

    while queue:
        current = queue.pop(0)
        if current not in visited:
            visited.add(current)
            queue.extend([neighbor for neighbor in graph[current] if neighbor not in visited])

    # All polygons should be connected
    return len(visited) == len(gdf)

# Example usage:
if __name__ == "__main__":
    # Create sample data
    from shapely.geometry import Polygon

    # Sample polygons
    polygons = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
        Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),
        Polygon([(3, 3), (4, 3), (4, 4), (3, 4)])  # Isolated polygon
    ]

    gdf = gpd.GeoDataFrame({
        'id': range(4),
        'value': ['A', 'B', 'C', 'D']
    }, geometry=polygons)

    print("Original GeoDataFrame:")
    print(gdf)

    # 1. Find touching polygons
    touching_pairs = find_touching_polygons(gdf)
    print(f"\nTouching polygon pairs: {touching_pairs}")

    # 2. Merge polygons
    try:
        # Merge polygons 0, 1, and 2 (they form a connected group)
        result_gdf = merge_polygons(gdf, [0, 1, 2])
        print(f"\nAfter merging polygons [0, 1, 2]:")
        print(result_gdf)

        # Verify area preservation
        original_area = gdf.loc[[0, 1, 2]].geometry.area.sum()
        merged_area = result_gdf.iloc[-1].geometry.area
        print(f"Original area: {original_area}, Merged area: {merged_area}")

    except ValueError as e:
        print(f"Merge failed: {e}")
