import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

def identify_slivers(gdf, base_polygon_gdf, buffer_distance=0.001, sliver_threshold=5):
    """
    Identify all touching polygon slivers for a given base polygon GeoDataFrame.

    Parameters:
    -----------
    gdf : GeoDataFrame
        Input GeoDataFrame containing multiple polygons
    base_polygon_gdf : GeoDataFrame
        GeoDataFrame containing the base polygon (should have exactly one geometry)
    buffer_distance : float, default=0.001
        Buffer distance to find nearly touching polygons
    sliver_threshold : float, default=5
        Area/Length ratio threshold (slivers have ratio < threshold)

    Returns:
    --------
    GeoDataFrame containing the identified sliver polygons
    """

    # Validate base_polygon_gdf
    if len(base_polygon_gdf) != 1:
        raise ValueError("base_polygon_gdf must contain exactly one geometry")

    # Extract the base polygon geometry
    base_polygon = base_polygon_gdf.geometry.iloc[0]
    base_polygon_index = base_polygon_gdf.index[0] if base_polygon_gdf.index.name else None

    # Create a copy to avoid modifying original
    working_gdf = gdf.copy()
    #working_gdf = gdf.explode().copy()

    # Find polygons that touch or are within buffer distance of base_polygon
    buffered_base = base_polygon.buffer(buffer_distance)

    # Find potential slivers (excluding the base polygon itself)
    if base_polygon_index is not None and base_polygon_index in working_gdf.index:
        potential_slivers = working_gdf[
            (working_gdf.geometry.intersects(buffered_base)) &
            (working_gdf.index != base_polygon_index)
        ].copy()
    else:
        # If we can't find by index, find by geometry equality
        potential_slivers = working_gdf[
            (working_gdf.geometry.intersects(buffered_base)) &
            (working_gdf.geometry != base_polygon)
        ].copy()

    if len(potential_slivers) == 0:
        print("No potential slivers found near the base polygon")
        return gpd.GeoDataFrame(geometry=[], crs=gdf.crs)

    # Calculate area/length ratio for each potential sliver
    potential_slivers['area'] = potential_slivers.geometry.area
    potential_slivers['length'] = potential_slivers.geometry.length
    potential_slivers['area_length_ratio'] = potential_slivers['area'] / potential_slivers['length']

    # Identify slivers based on threshold
    slivers = potential_slivers[potential_slivers['area_length_ratio'] < sliver_threshold].copy()

    print(f"Found {len(slivers)} sliver polygons out of {len(potential_slivers)} potential candidates (Sliver Criterion: Area/Length < {sliver_threshold}m)")

    # Add sliver information
    slivers['is_sliver'] = True
    slivers['sliver_ratio'] = slivers['area_length_ratio']

    return slivers[['geometry', 'is_sliver', 'sliver_ratio', 'area', 'length']]


def merge_slivers_into_base(gdf, base_polygon_gdf, slivers_gdf, buffer_distance=0.001, preserve_attributes=True):
    """
    Merge identified slivers into the base polygon and return updated GeoDataFrame.

    Parameters:
    -----------
    gdf : GeoDataFrame
        Original GeoDataFrame
    base_polygon_gdf : GeoDataFrame
        GeoDataFrame containing the base polygon (should have exactly one geometry)
    slivers_gdf : GeoDataFrame
        Slivers identified by identify_slivers function
    buffer_distance : float, default=0.001
        Buffer distance for robust merging
    preserve_attributes : bool, default=True
        Whether to preserve attributes from the base polygon

    Returns:
    --------
    GeoDataFrame with slivers merged into base polygon
    """

    # Validate base_polygon_gdf
    if len(base_polygon_gdf) != 1:
        raise ValueError("base_polygon_gdf must contain exactly one geometry")

    # Extract base polygon information
    base_polygon = base_polygon_gdf.geometry.iloc[0]
    base_polygon_index = base_polygon_gdf.index[0]
    base_polygon_attributes = base_polygon_gdf.iloc[0].drop('geometry').to_dict() if preserve_attributes else {}

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
        print("Merged geometry resulted in MultiPolygon - using largest component")
    elif final_merged_geometry.geom_type != 'Polygon':
        # If geometry type is unexpected, fall back to original base_polygon
        print(f"Warning: Unexpected geometry type after merging: {final_merged_geometry.geom_type}")
        final_merged_geometry = base_polygon

    # Update the base polygon in the GeoDataFrame
    if base_polygon_index in updated_gdf.index:
        # Update existing base polygon
        updated_gdf.loc[base_polygon_index, 'geometry'] = final_merged_geometry
        if preserve_attributes:
            # Update other attributes if needed
            for attr, value in base_polygon_attributes.items():
                if attr in updated_gdf.columns:
                    updated_gdf.loc[base_polygon_index, attr] = value
    else:
        # If base polygon is not in the original GDF, add it
        new_row = base_polygon_gdf.copy()
        new_row.geometry = final_merged_geometry
        updated_gdf = pd.concat([updated_gdf, new_row], ignore_index=True)

    # Remove the sliver polygons from the GeoDataFrame
    sliver_indices = slivers_gdf.index
    updated_gdf = updated_gdf.drop(sliver_indices, errors='ignore')

    # Reset index if we have duplicate indices
    if updated_gdf.index.duplicated().any():
        updated_gdf = updated_gdf.reset_index(drop=True)

    print(f"Successfully merged {len(slivers_gdf)} slivers into base polygon")
    print(f"Updated GeoDataFrame has {len(updated_gdf)} polygons (original had {len(gdf)})")

    return updated_gdf




