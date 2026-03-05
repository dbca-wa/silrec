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

    #import ipdb; ipdb.set_trace()
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



