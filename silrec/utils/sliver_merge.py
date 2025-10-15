import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

def find_largest_neighbor(target_gdf, full_gdf):
    """
    Find the largest neighboring/touching polygon for a given target polygon.

    Parameters:
    -----------
    target_gdf : GeoDataFrame
        Single-row GeoDataFrame containing the target polygon
    full_gdf : GeoDataFrame
        Full GeoDataFrame containing all polygons

    Returns:
    --------
    GeoDataFrame
        Single-row GeoDataFrame containing the largest neighbor
    """
    if len(target_gdf) != 1:
        raise ValueError("target_gdf must contain exactly one row")

    target_geom = target_gdf.geometry.iloc[0]
    target_idx = target_gdf.index[0]

    # Find all polygons that touch/intersect with the target (excluding itself)
    neighbors_mask = full_gdf.geometry.apply(
        lambda geom: (geom.touches(target_geom) or geom.intersects(target_geom))
    )

    # Exclude the target polygon itself
    neighbors_mask = neighbors_mask & (full_gdf.index != target_idx)

    neighbors = full_gdf[neighbors_mask]

    if len(neighbors) == 0:
        return None

    # Find the largest neighbor by area
    largest_neighbor_idx = neighbors.geometry.area.idxmax()
    largest_neighbor = full_gdf.loc[[largest_neighbor_idx]]

    return largest_neighbor

def merge_target_into_neighbor(target_gdf, neighbor_gdf, full_gdf):
    """
    Merge target polygon into its neighbor and return updated GeoDataFrame.
    The target polygon is removed and the neighbor grows to include the target.

    Parameters:
    -----------
    target_gdf : GeoDataFrame
        Single-row GeoDataFrame containing the target polygon to be removed
    neighbor_gdf : GeoDataFrame
        Single-row GeoDataFrame containing the neighbor polygon to grow
    full_gdf : GeoDataFrame
        Full GeoDataFrame containing all polygons

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with target removed and neighbor merged
    """
    if len(target_gdf) != 1 or len(neighbor_gdf) != 1:
        raise ValueError("Both target_gdf and neighbor_gdf must contain exactly one row")

    target_idx = target_gdf.index[0]
    neighbor_idx = neighbor_gdf.index[0]

    # Create a copy to avoid modifying the original
    updated_gdf = full_gdf.copy()

    # Merge the geometries (target into neighbor)
    merged_geometry = unary_union([
        updated_gdf.loc[neighbor_idx].geometry,
        updated_gdf.loc[target_idx].geometry
    ])

    # Update the NEIGHBOR polygon with the merged geometry
    updated_gdf.loc[neighbor_idx, 'geometry'] = merged_geometry

    # Remove the TARGET polygon
    updated_gdf = updated_gdf.drop(target_idx)

    return updated_gdf

#def find_and_merge(target_gdf, full_gdf):
def find_and_merge(full_gdf, sliver_threshold):
    """
    Iterate through each target polygon, find its largest neighbor, and merge the target into that neighbor.
    Returns updated GeoDataFrame with reduced polygon count.

    Parameters:
    -----------
    target_gdf : GeoDataFrame
        GeoDataFrame containing target polygons to be merged into their neighbors
    full_gdf : GeoDataFrame
        Full GeoDataFrame containing all polygons
    sliver_threshold:
        Area per unit Length threshold
        gdf.area/gdf.length < sliver_threshold
    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with target polygons merged into their largest neighbors
    """
    target_gdf = full_gdf[full_gdf.area/full_gdf.length < sliver_threshold]

    if len(target_gdf) == 0:
        return full_gdf.copy()

    # Start with a copy of the full GeoDataFrame
    current_gdf = full_gdf.copy()

    # Track which targets we've processed to avoid issues with changing indices
    targets_to_process = target_gdf.index.tolist()
    processed_count = 0

    for target_idx in targets_to_process:
        # Check if target still exists in current_gdf (might have been processed as a neighbor earlier)
        if target_idx not in current_gdf.index:
            continue

        # Get current version of the target
        current_target = current_gdf.loc[[target_idx]]

        # Find largest neighbor for this target
        largest_neighbor = find_largest_neighbor(current_target, current_gdf)

        if largest_neighbor is not None:
            neighbor_idx = largest_neighbor.index[0]

            # Only merge if neighbor still exists and is different from target
            if neighbor_idx in current_gdf.index and neighbor_idx != target_idx:
                print(f"Merging target {target_idx} into neighbor {neighbor_idx}")
                current_gdf = merge_target_into_neighbor(
                    current_target,
                    largest_neighbor,
                    current_gdf
                )
                processed_count += 1
            else:
                print(f"Skipping target {target_idx} - neighbor no longer available")
        else:
            print(f"Skipping target {target_idx} - no neighbors found")

    print(f"Successfully merged {processed_count} out of {len(targets_to_process)} target polygons")
    print(f"Polygon count reduced from {len(full_gdf)} to {len(current_gdf)}")

    return current_gdf

# Example usage and demonstration:
if __name__ == "__main__":
    # Create sample data with multiple target polygons
    from shapely.geometry import Polygon

    # Sample polygons - creating connected polygons
    polygons = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),      # Target 1 - will be merged into neighbor
        Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),      # Will receive Target 1 (largest neighbor)
        Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),      # Target 2 - will be merged into neighbor
        Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),      # Will receive Target 2 (largest neighbor)
        Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),      # Isolated polygon (not a target)
        Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),      # Another polygon (not a target)
    ]

    gdf1 = gpd.GeoDataFrame({
        'id': range(6),
        'type': ['target', 'receiver', 'target', 'receiver', 'isolated', 'other'],
        'value': [10, 20, 30, 40, 50, 60]
    }, geometry=polygons)

    print("Original GeoDataFrame:")
    print(gdf1[['id', 'type', 'value']])
    print(f"Original number of polygons: {len(gdf1)}")
    print(f"Original areas: {[round(g.area, 2) for g in gdf1.geometry]}")

    # Define target polygons (the ones we want to merge into their neighbors)
    target_polygons = gdf1[gdf1['type'] == 'target']
    print(f"\nTarget polygons to process: {len(target_polygons)}")

    # Perform the merging
    merged_gdf = find_and_merge(target_polygons, gdf1)

    print("\n--- Results ---")
    print(f"Final number of polygons: {len(merged_gdf)}")
    print(f"Expected reduction: {len(gdf1) - len(target_polygons)} polygons")
    print(f"Actual reduction: {len(gdf1) - len(merged_gdf)} polygons")

    print("\nMerged GeoDataFrame:")
    print(merged_gdf[['id', 'type', 'value']])
    print(f"Final areas: {[round(g.area, 2) for g in merged_gdf.geometry]}")

    # Verify the results
    print("\n--- Verification ---")
    print(f"Target polygons in result: {len(merged_gdf[merged_gdf['type'] == 'target'])}")
    print(f"Receiver polygons grew from {gdf1.iloc[1].geometry.area:.2f} to {merged_gdf.iloc[0].geometry.area:.2f}")
    print(f"Receiver polygons grew from {gdf1.iloc[3].geometry.area:.2f} to {merged_gdf.iloc[1].geometry.area:.2f}")
