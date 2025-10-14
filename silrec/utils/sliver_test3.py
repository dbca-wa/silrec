import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from django.conf import settings

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

    # Find all polygons that touch/intersect with the target (excluding itself)
    neighbors_mask = full_gdf.geometry.apply(
        lambda geom: geom.touches(target_geom) or geom.intersects(target_geom)
    )

    # Exclude the target polygon itself
    neighbors_mask = neighbors_mask & (full_gdf.index != target_gdf.index[0])

    neighbors = full_gdf[neighbors_mask]

    if len(neighbors) == 0:
        raise ValueError("No neighboring polygons found")

    # Find the largest neighbor by area
    largest_neighbor_idx = neighbors.geometry.area.idxmax()
    largest_neighbor = full_gdf.loc[[largest_neighbor_idx]]

    return largest_neighbor

def merge_polygons(target_gdf, neighbor_gdf, full_gdf):
    """
    Merge the target polygon with its largest neighbor and return updated GeoDataFrame.

    Parameters:
    -----------
    target_gdf : GeoDataFrame
        Single-row GeoDataFrame containing the target polygon
    neighbor_gdf : GeoDataFrame
        Single-row GeoDataFrame containing the neighbor polygon to merge with
    full_gdf : GeoDataFrame
        Full GeoDataFrame containing all polygons

    Returns:
    --------
    GeoDataFrame
        Updated GeoDataFrame with the two polygons merged into one
    """
    if len(target_gdf) != 1 or len(neighbor_gdf) != 1:
        raise ValueError("Both target_gdf and neighbor_gdf must contain exactly one row")

    target_idx = target_gdf.index[0]
    neighbor_idx = neighbor_gdf.index[0]

    # Create a copy to avoid modifying the original
    updated_gdf = full_gdf.copy()

    # Merge the geometries
    merged_geometry = unary_union([
        updated_gdf.loc[target_idx].geometry,
        updated_gdf.loc[neighbor_idx].geometry
    ])

    # Update the target polygon with the merged geometry
    updated_gdf.loc[target_idx, 'geometry'] = merged_geometry

    # Remove the neighbor polygon
    updated_gdf = updated_gdf.drop(neighbor_idx)

    # Reset index if desired (optional)
    # updated_gdf = updated_gdf.reset_index(drop=True)

    return updated_gdf

# Alternative: Combined function that does both operations
def find_and_merge(target_gdf, full_gdf):
    """
    Find the largest neighbor and merge it with the target polygon in one step.

    Parameters:
    -----------
    target_gdf : GeoDataFrame
        Single-row GeoDataFrame containing the target polygon
    full_gdf : GeoDataFrame
        Full GeoDataFrame containing all polygons

    Returns:
    --------
    tuple
        (merged_gdf, largest_neighbor_gdf) - updated GeoDataFrame and the neighbor that was merged
    """
    largest_neighbor = find_largest_neighbor(target_gdf, full_gdf)
    merged_gdf = merge_polygons(target_gdf, largest_neighbor, full_gdf)

    return merged_gdf, largest_neighbor

def find_and_merge2(target_gdf, full_gdf):
    """
    Find the largest neighbor and merge it with the target polygon in one step.

    Parameters:
    -----------
    target_gdf : GeoDataFrame
        Single-row GeoDataFrame containing the target polygon
    full_gdf : GeoDataFrame
        Full GeoDataFrame containing all polygons

    Returns:
    --------
    tuple
        (merged_gdf, largest_neighbor_gdf) - updated GeoDataFrame and the neighbor that was merged
    """
    gdf_merged = full_gdf.copy()
    for index, row in target_gdf.iterrows():
        #import ipdb; ipdb.set_trace()
        gdf_single = gpd.GeoDataFrame([row], geometry=[row.geometry], crs=settings.CRS_GDA94)
        largest_neighbor = find_largest_neighbor(gdf_single, gdf_merged)
        gdf_merged = merge_polygons(gdf_single, largest_neighbor, gdf_merged)

    return gdf_merged


# Example usage:
if __name__ == "__main__":
    # Create sample data for demonstration
    from shapely.geometry import Polygon

    # Sample polygons
    polygons = [
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),  # Target polygon
        Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),  # Neighbor 1 (touching)
        Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),  # Neighbor 2 (touching, larger)
        Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),  # Non-touching polygon
    ]

    gdf1 = gpd.GeoDataFrame({'id': range(4), 'value': ['A', 'B', 'C', 'D']},
                           geometry=polygons)

    # Get target polygon (first one)
    target_polygon = gdf1.iloc[[0]]
    print("Target polygon area:", target_polygon.geometry.area.iloc[0])

    # Find largest neighbor
    largest_neighbor = find_largest_neighbor(target_polygon, gdf1)
    print("Largest neighbor area:", largest_neighbor.geometry.area.iloc[0])
    print("Largest neighbor id:", largest_neighbor['id'].iloc[0])

    # Merge polygons
    merged_gdf = merge_polygons(target_polygon, largest_neighbor, gdf1)
    print(f"Original had {len(gdf1)} polygons, merged has {len(merged_gdf)} polygons")
    print("Merged polygon area:", merged_gdf.iloc[0].geometry.area)

    # Or use the combined function
    merged_gdf2, neighbor_gdf = find_and_merge(target_polygon, gdf1)
    print(f"Combined function result: {len(merged_gdf2)} polygons")
