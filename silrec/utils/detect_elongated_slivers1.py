import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
from shapely.ops import split, unary_union
from scipy.spatial import distance
import math

def calculate_aspect_ratio(polygon):
    """
    Calculate aspect ratio of a polygon's minimum bounding rectangle.
    Higher values indicate more elongated shapes.
    """
    if polygon.is_empty:
        return 0

    # Get minimum rotated rectangle
    mbr = polygon.minimum_rotated_rectangle

    # Get coordinates of MBR
    mbr_coords = list(mbr.exterior.coords)

    # Calculate side lengths
    sides = []
    for i in range(4):
        p1 = mbr_coords[i]
        p2 = mbr_coords[(i + 1) % 4]
        side_length = distance.euclidean(p1, p2)
        sides.append(side_length)

    # Sort sides and calculate aspect ratio (longest/shortest)
    sides_sorted = sorted(sides)
    if sides_sorted[0] > 0:
        return sides_sorted[-1] / sides_sorted[0]
    return 0

def identify_slivers(polygon, aspect_ratio_threshold=10, area_ratio_threshold=0.1):
    """
    Identify sliver polygons by decomposing and analyzing parts.

    Parameters:
    - polygon: Shapely Polygon
    - aspect_ratio_threshold: Minimum aspect ratio to consider as sliver
    - area_ratio_threshold: Maximum area ratio (sliver area / total area) to consider as sliver

    Returns:
    - tuple: (slivers, main_polygons) as lists of Polygons
    """
    if not isinstance(polygon, Polygon) or polygon.is_empty:
        return [], []

    # Decompose polygon into convex parts for analysis
    try:
        # Use buffer(0) to fix potential self-intersection issues
        cleaned_poly = polygon.buffer(0)
        if cleaned_poly.is_empty:
            return [], []

        # If it becomes a MultiPolygon after cleaning, handle each part
        if isinstance(cleaned_poly, MultiPolygon):
            polygons = list(cleaned_poly.geoms)
        else:
            polygons = [cleaned_poly]

    except:
        polygons = [polygon]

    slivers = []
    main_polygons = []
    total_area = polygon.area

    for poly in polygons:
        aspect_ratio = calculate_aspect_ratio(poly)
        area_ratio = poly.area / total_area if total_area > 0 else 1

        # Check if this part qualifies as a sliver
        if (aspect_ratio >= aspect_ratio_threshold and
            area_ratio <= area_ratio_threshold):
            slivers.append(poly)
        else:
            main_polygons.append(poly)

    return slivers, main_polygons

def separate_slivers_geometry(geometry, aspect_ratio_threshold=10, area_ratio_threshold=0.1):
    """
    Separate slivers from any Shapely geometry type.

    Returns:
    - tuple: (main_geometry, slivers_geometry)
    """
    if isinstance(geometry, Polygon):
        slivers, main_parts = identify_slivers(
            geometry, aspect_ratio_threshold, area_ratio_threshold
        )

        # Create appropriate geometry types
        if len(main_parts) == 0:
            main_geometry = None
        elif len(main_parts) == 1:
            main_geometry = main_parts[0]
        else:
            main_geometry = MultiPolygon(main_parts)

        if len(slivers) == 0:
            slivers_geometry = None
        elif len(slivers) == 1:
            slivers_geometry = slivers[0]
        else:
            slivers_geometry = MultiPolygon(slivers)

        return main_geometry, slivers_geometry

    elif isinstance(geometry, MultiPolygon):
        all_slivers = []
        all_main_parts = []

        for poly in geometry.geoms:
            slivers, main_parts = identify_slivers(
                poly, aspect_ratio_threshold, area_ratio_threshold
            )
            all_slivers.extend(slivers)
            all_main_parts.extend(main_parts)

        # Create appropriate geometry types
        main_geometry = MultiPolygon(all_main_parts) if all_main_parts else None
        slivers_geometry = MultiPolygon(all_slivers) if all_slivers else None

        return main_geometry, slivers_geometry

    else:
        # Return original geometry for non-polygon types
        return geometry, None

def separate_slivers_gdf(gdf, aspect_ratio_threshold=10, area_ratio_threshold=0.1,
                        geometry_column='geometry', inplace=False):
    """
    Main function to separate slivers from a GeoDataFrame.

    Parameters:
    - gdf: GeoDataFrame
    - aspect_ratio_threshold: Minimum aspect ratio for sliver detection
    - area_ratio_threshold: Maximum area ratio for sliver detection
    - geometry_column: Name of geometry column
    - inplace: Whether to modify the original GeoDataFrame

    Returns:
    - GeoDataFrame with slivers separated into new rows
    """
    if not inplace:
        gdf = gdf.copy()

    # Lists to store new rows
    new_rows = []

    for idx, row in gdf.iterrows():
        geometry = row[geometry_column]

        if geometry is None or geometry.is_empty:
            continue

        main_geom, slivers_geom = separate_slivers_geometry(
            geometry, aspect_ratio_threshold, area_ratio_threshold
        )

        # Update original row with main geometry
        if main_geom is not None:
            row[geometry_column] = main_geom
        else:
            # If no main geometry remains, mark for deletion
            row[geometry_column] = None

        # Add slivers as new rows
        if slivers_geom is not None:
            if isinstance(slivers_geom, (Polygon, MultiPolygon)):
                # Create new row for each sliver polygon
                sliver_polygons = (
                    slivers_geom.geoms if isinstance(slivers_geom, MultiPolygon)
                    else [slivers_geom]
                )

                for sliver in sliver_polygons:
                    new_row = row.copy()
                    new_row[geometry_column] = sliver
                    # Add sliver identifier
                    if 'sliver' not in new_row:
                        new_row['is_sliver'] = True
                    new_rows.append(new_row)

    # Remove rows with null geometries
    gdf = gdf[gdf[geometry_column].notna() & ~gdf[geometry_column].is_empty]

    # Add new sliver rows
    if new_rows:
        slivers_gdf = gpd.GeoDataFrame(new_rows, crs=gdf.crs)
        result_gdf = gpd.GeoDataFrame(
            pd.concat([gdf, slivers_gdf], ignore_index=True),
            crs=gdf.crs
        )
    else:
        result_gdf = gdf

    return result_gdf

def separate_slivers_to_new_gdf(gdf, aspect_ratio_threshold=10, area_ratio_threshold=0.1,
                               geometry_column='geometry'):
    """
    Separate slivers into a completely new GeoDataFrame.

    Returns:
    - tuple: (main_gdf, slivers_gdf)
    """
    main_rows = []
    sliver_rows = []

    for idx, row in gdf.iterrows():
        geometry = row[geometry_column]

        if geometry is None or geometry.is_empty:
            continue

        main_geom, slivers_geom = separate_slivers_geometry(
            geometry, aspect_ratio_threshold, area_ratio_threshold
        )

        # Add main geometry row
        if main_geom is not None:
            main_row = row.copy()
            main_row[geometry_column] = main_geom
            main_row['is_sliver'] = False
            main_rows.append(main_row)

        # Add sliver rows
        if slivers_geom is not None:
            sliver_polygons = (
                slivers_geom.geoms if isinstance(slivers_geom, MultiPolygon)
                else [slivers_geom]
            )

            for sliver in sliver_polygons:
                sliver_row = row.copy()
                sliver_row[geometry_column] = sliver
                sliver_row['is_sliver'] = True
                sliver_rows.append(sliver_row)

    # Create GeoDataFrames
    main_gdf = gpd.GeoDataFrame(main_rows, crs=gdf.crs) if main_rows else None
    slivers_gdf = gpd.GeoDataFrame(sliver_rows, crs=gdf.crs) if sliver_rows else None

    return main_gdf, slivers_gdf

# Example usage:
if __name__ == "__main__":
    # Create example data
    from shapely.geometry import Polygon

    # Example polygon with a sliver
    polygon_with_sliver = Polygon([
        (0, 0), (10, 0), (10, 1), (9, 1), (9, 0.1), (8, 0.1),
        (8, 1), (0, 1), (0, 0)
    ])

    gdf = gpd.GeoDataFrame({'id': [1]}, geometry=[polygon_with_sliver])

    # Separate slivers
    result_gdf = separate_slivers_gdf(
        gdf,
        aspect_ratio_threshold=8,  # Adjust based on your needs
        area_ratio_threshold=0.05  # Adjust based on your needs
    )

    print(f"Original: {len(gdf)} features")
    print(f"After separation: {len(result_gdf)} features")

    # Or separate into two separate GeoDataFrames
    main_gdf, slivers_gdf = separate_slivers_to_new_gdf(gdf)

    if main_gdf is not None:
        print(f"Main polygons: {len(main_gdf)}")
    if slivers_gdf is not None:
        print(f"Slivers: {len(slivers_gdf)}")
