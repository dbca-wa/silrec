import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd
from shapely.ops import unary_union
import numpy as np

class SliverProcessor:
    """
    A class to process and merge sliver polygons from intersection results.
    """

    def __init__(self, result_gdf, gdf2_excl, combined_gdf, slivers_gdf):
        """
        Initialize the SliverProcessor with classified intersection results.
        """
        self.result_gdf = result_gdf.copy()
        self.gdf2_excl = gdf2_excl.copy()
        self.combined_gdf = combined_gdf.copy()
        self.slivers_gdf = slivers_gdf.copy()
        self.original_crs = combined_gdf.crs

        # Validate input
        self._validate_input()

    def _validate_input(self):
        """Validate input GeoDataFrames."""
        required_columns = ['poly_type']
        for gdf_name in ['combined_gdf', 'result_gdf', 'gdf2_excl']:
            gdf = getattr(self, gdf_name)
            for col in required_columns:
                if col not in gdf.columns:
                    raise ValueError(f"'{col}' column missing from {gdf_name}")

    def _find_neighbors_by_longest_boundary(self, target_polygon, target_index, search_gdf):
        """
        Find neighbors sorted by the length of shared boundary.
        Returns list of tuples: (neighbor_index, shared_boundary_length, neighbor_poly_type)
        """
        neighbors = []

        for idx, row in search_gdf.iterrows():
            if idx == target_index:
                continue

            neighbor_poly = row.geometry
            if target_polygon.touches(neighbor_poly):
                # Calculate shared boundary length
                shared_boundary = target_polygon.intersection(neighbor_poly.boundary)
                if shared_boundary.geom_type == 'MultiLineString':
                    shared_length = sum(line.length for line in shared_boundary.geoms)
                else:
                    shared_length = shared_boundary.length

                neighbors.append((idx, shared_length, row['poly_type']))

        # Sort by boundary length (longest first) and poly_type preference
        neighbors.sort(key=lambda x: (
            x[2] != 'BASE',  # Prefer BASE neighbors (False comes first)
            -x[1]  # Then by boundary length (longest first)
        ))

        return neighbors

    def _merge_polygons_by_ids(self, polygon_ids, original_gdf):
        """
        Merge specified polygons by their IDs.
        """
        if len(polygon_ids) == 0:
            return None, {}

        # Get polygons to merge
        polygons_to_merge = original_gdf.loc[polygon_ids]

        # Merge geometries using unary_union
        try:
            merged_geometry = unary_union(polygons_to_merge.geometry.tolist())

            # If we get a MultiPolygon, try to extract the largest valid polygon
            if merged_geometry.geom_type == 'MultiPolygon':
                valid_polygons = [poly for poly in merged_geometry.geoms if poly.is_valid and poly.area > 0]
                if valid_polygons:
                    # Use the largest valid polygon
                    areas = [poly.area for poly in valid_polygons]
                    largest_idx = np.argmax(areas)
                    merged_geometry = valid_polygons[largest_idx]
                else:
                    # Fallback: use convex hull of the original polygons
                    merged_geometry = unary_union(polygons_to_merge.geometry.tolist()).convex_hull

            # Ensure the geometry is valid
            if not merged_geometry.is_valid:
                merged_geometry = merged_geometry.buffer(0)  # Try to fix validity

        except Exception as e:
            print(f"  Geometry merge error: {e}")
            # Fallback: use the largest polygon from the set
            areas = polygons_to_merge.geometry.area
            largest_idx = areas.idxmax()
            merged_geometry = polygons_to_merge.loc[largest_idx, 'geometry']

        # Combine attributes
        combined_attrs = self._combine_attributes(polygons_to_merge)

        return merged_geometry, combined_attrs

    def _combine_attributes(self, polygons_to_merge):
        """Combine attributes from multiple polygons."""
        combined_attrs = {}

        for col in polygons_to_merge.columns:
            if col == 'geometry':
                continue

            # Handle special columns
            if col == 'source_gdf1_id':
                unique_values = polygons_to_merge[col].dropna().unique()
                combined_attrs[col] = unique_values[0] if len(unique_values) == 1 else None
                continue

            # For numeric columns, take weighted average by area
            if pd.api.types.is_numeric_dtype(polygons_to_merge[col]):
                total_area = polygons_to_merge.geometry.area.sum()
                if total_area > 0:
                    weighted_sum = (polygons_to_merge[col] * polygons_to_merge.geometry.area).sum()
                    combined_attrs[col] = weighted_sum / total_area
                else:
                    combined_attrs[col] = polygons_to_merge[col].mean()
            else:
                # For categorical/string columns, take the most frequent value
                value_counts = polygons_to_merge[col].value_counts()
                if len(value_counts) > 0:
                    combined_attrs[col] = value_counts.index[0]
                else:
                    combined_attrs[col] = None

        # Smart poly_type assignment
        if 'poly_type' in combined_attrs:
            poly_types = polygons_to_merge['poly_type'].unique()

            # Priority: BASE > CUT > HIST > SLVR
            if 'BASE' in poly_types:
                combined_attrs['poly_type'] = 'BASE'
            elif 'CUT' in poly_types:
                combined_attrs['poly_type'] = 'CUT'
            elif 'HIST' in poly_types:
                combined_attrs['poly_type'] = 'HIST'
            else:
                # All are SLVR (shouldn't happen in our use case)
                combined_attrs['poly_type'] = 'BASE'  # Upgrade to BASE

        combined_attrs['merged_from'] = f"merged_{len(polygons_to_merge)}_polygons"
        combined_attrs['original_ids'] = list(polygons_to_merge.index)

        return combined_attrs

    def auto_merge_all_slivers(self, area_tolerance=0.001):
        """
        Merge ALL SLVR polygons into their neighbors with preference for BASE polygons
        and longest shared boundaries.

        Parameters:
        -----------
        area_tolerance : float
            Maximum allowed area difference as fraction of total area

        Returns:
        --------
        GeoDataFrame
            New combined_gdf with ALL slivers merged
        """
        print("Starting comprehensive sliver merge...")

        # Create working copy with reset index
        working_gdf = self.combined_gdf.reset_index(drop=True)
        original_area = working_gdf.geometry.area.sum()
        print(f"Original total area: {original_area:.10f}")
        print(f"Original SLVR count: {(working_gdf['poly_type'] == 'SLVR').sum()}")

        # Continue merging until no SLVR polygons remain
        iteration = 0
        max_iterations = 10  # Safety limit

        while (working_gdf['poly_type'] == 'SLVR').sum() > 0 and iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            print(f"SLVR polygons remaining: {(working_gdf['poly_type'] == 'SLVR').sum()}")

            working_gdf = self._merge_slivers_iteration(working_gdf, area_tolerance)

            # Safety check
            if len(working_gdf) == 0:
                raise ValueError("All polygons were removed during merging!")

        if iteration == max_iterations:
            print("WARNING: Maximum iterations reached. Some SLVR polygons may remain.")

        final_sliver_count = (working_gdf['poly_type'] == 'SLVR').sum()
        if final_sliver_count > 0:
            print(f"WARNING: {final_sliver_count} SLVR polygons could not be merged")

        # Final area verification
        new_area = working_gdf.geometry.area.sum()
        area_diff = abs(original_area - new_area)
        area_diff_percent = (area_diff / original_area * 100) if original_area > 0 else 0

        print(f"\n=== Final Results ===")
        print(f"Total iterations: {iteration}")
        print(f"Remaining SLVR polygons: {final_sliver_count}")
        print(f"Final polygon count: {len(working_gdf)}")
        print(f"Area preservation: {area_diff_percent:.6f}% difference")

        if area_diff_percent > area_tolerance * 100:
            print("WARNING: Significant area change detected!")

        return working_gdf

    def _merge_slivers_iteration(self, working_gdf, area_tolerance):
        """
        Perform one iteration of sliver merging.
        """
        sliver_mask = working_gdf['poly_type'] == 'SLVR'
        sliver_indices = working_gdf[sliver_mask].index.tolist()

        processed_indices = set()
        merge_operations = []
        failed_merges = []

        # Process each sliver
        for sliver_idx in sliver_indices:
            if sliver_idx in processed_indices:
                continue

            sliver_poly = working_gdf.loc[sliver_idx, 'geometry']
            sliver_area = sliver_poly.area

            # Find all potential neighbors (excluding other SLVRs for now)
            non_sliver_mask = working_gdf['poly_type'] != 'SLVR'
            neighbors = self._find_neighbors_by_longest_boundary(
                sliver_poly, sliver_idx, working_gdf[non_sliver_mask]
            )

            if neighbors:
                # Get the best neighbor (first in sorted list)
                best_neighbor_idx, shared_length, neighbor_poly_type = neighbors[0]

                # Check if neighbor is already processed
                if best_neighbor_idx in processed_indices:
                    # Try the next best neighbor
                    for neighbor_idx, _, _ in neighbors[1:]:
                        if neighbor_idx not in processed_indices:
                            best_neighbor_idx = neighbor_idx
                            break
                    else:
                        # No unprocessed neighbors found
                        continue

                polygons_to_merge = [sliver_idx, best_neighbor_idx]

                try:
                    merged_geometry, combined_attrs = self._merge_polygons_by_ids(
                        polygons_to_merge, working_gdf
                    )

                    if merged_geometry and merged_geometry.is_valid and merged_geometry.area > 0:
                        # Verify area preservation
                        original_merged_area = working_gdf.loc[polygons_to_merge].geometry.area.sum()
                        new_area = merged_geometry.area
                        area_diff = abs(original_merged_area - new_area)

                        if area_diff / original_merged_area < area_tolerance:
                            merge_operations.append({
                                'remove_indices': polygons_to_merge,
                                'new_geometry': merged_geometry,
                                'new_attributes': combined_attrs
                            })

                            processed_indices.update(polygons_to_merge)
                            print(f"  Merged SLVR {sliver_idx} (area: {sliver_area:.6f}) with {neighbor_poly_type} {best_neighbor_idx} (shared: {shared_length:.4f})")
                        else:
                            failed_merges.append({
                                'indices': polygons_to_merge,
                                'reason': f'Area mismatch: {area_diff/original_merged_area*100:.4f}%'
                            })
                    else:
                        failed_merges.append({
                            'indices': polygons_to_merge,
                            'reason': 'Invalid geometry after merge'
                        })

                except Exception as e:
                    failed_merges.append({
                        'indices': polygons_to_merge,
                        'reason': f'Merge error: {str(e)}'
                    })
            else:
                # No non-SLVR neighbors found, try merging with other SLVRs
                sliver_neighbors = self._find_neighbors_by_longest_boundary(
                    sliver_poly, sliver_idx, working_gdf[sliver_mask]
                )

                if sliver_neighbors:
                    best_sliver_idx, shared_length, _ = sliver_neighbors[0]

                    if best_sliver_idx not in processed_indices:
                        polygons_to_merge = [sliver_idx, best_sliver_idx]

                        try:
                            merged_geometry, combined_attrs = self._merge_polygons_by_ids(
                                polygons_to_merge, working_gdf
                            )

                            if merged_geometry and merged_geometry.is_valid:
                                merge_operations.append({
                                    'remove_indices': polygons_to_merge,
                                    'new_geometry': merged_geometry,
                                    'new_attributes': combined_attrs
                                })

                                processed_indices.update(polygons_to_merge)
                                print(f"  Merged SLVR {sliver_idx} with SLVR {best_sliver_idx} (shared: {shared_length:.4f})")

                        except Exception as e:
                            failed_merges.append({
                                'indices': polygons_to_merge,
                                'reason': f'SLVR-SLVR merge error: {str(e)}'
                            })

        # Apply merge operations
        if merge_operations:
            # Create result dataframe starting with unprocessed polygons
            unprocessed_mask = ~working_gdf.index.isin(processed_indices)
            result_gdf = working_gdf[unprocessed_mask].copy()

            # Add new merged polygons
            new_rows = []
            for op in merge_operations:
                new_row = op['new_attributes'].copy()
                new_row['geometry'] = op['new_geometry']
                new_rows.append(new_row)

            if new_rows:
                new_gdf = gpd.GeoDataFrame(new_rows, crs=self.original_crs)
                result_gdf = pd.concat([result_gdf, new_gdf], ignore_index=True)

            print(f"  Applied {len(merge_operations)} merges, {len(failed_merges)} failed")
            return result_gdf
        else:
            print("  No merges possible in this iteration")
            return working_gdf


# Example usage:
if __name__ == "__main__":
    # Create sample data with multiple SLVR polygons
    from shapely.geometry import Polygon

    poly1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
    gdf1 = gpd.GeoDataFrame({'id': [1], 'name': ['main_polygon']},
                           geometry=[poly1], crs='EPSG:4326')

    # Create gdf2 with multiple slivers
    polygons2 = [
        Polygon([(1, 1), (4, 1), (4, 4), (1, 4)]),  # BASE
        Polygon([(2, 0), (5, 0), (5, 2), (2, 2)]),  # BASE
        Polygon([(0, 2), (2, 2), (2, 5), (0, 5)]),  # BASE
        # Multiple slivers
        Polygon([(2.9, 2.9), (3.0, 2.9), (3.0, 3.0), (2.9, 3.0)]),  # Small square sliver
        Polygon([(1.5, 2.9), (1.6, 2.9), (1.6, 3.1), (1.5, 3.1)]),  # Thin rectangle sliver
        Polygon([(2.8, 1.5), (2.9, 1.5), (2.9, 1.6), (2.8, 1.6)]),  # Another small sliver
    ]
    gdf2 = gpd.GeoDataFrame({
        'id': [10, 20, 30, 40, 50, 60],
        'type': ['A', 'B', 'C', 'D', 'E', 'F'],
        'value': [100, 200, 300, 400, 500, 600]
    }, geometry=polygons2, crs='EPSG:4326')

    # Use first class to get intersection results
    intersector = PolygonIntersector(gdf1, gdf2)
    intersector.calculate_intersections(method='enhanced')
    result_gdf, gdf2_excl, combined_gdf, slivers_gdf = intersector.get_classified_results(
        sliver_threshold=0.5,
        include_pre_existing_slivers=False
    )

    print("=== Initial State ===")
    print(f"Total polygons: {len(combined_gdf)}")
    print(f"SLVR polygons: {(combined_gdf['poly_type'] == 'SLVR').sum()}")
    print(f"Total area: {combined_gdf.geometry.area.sum():.10f}")

    # Use SliverProcessor
    processor = SliverProcessor(result_gdf, gdf2_excl, combined_gdf, slivers_gdf)

    # Merge ALL slivers
    print("\n=== Merging ALL SLVR Polygons ===")
    merged_gdf = processor.auto_merge_all_slivers(area_tolerance=0.001)

    print(f"\n=== Final Results ===")
    print(f"Final polygon count: {len(merged_gdf)}")
    print(f"Remaining SLVR polygons: {(merged_gdf['poly_type'] == 'SLVR').sum()}")
    print(f"Final area: {merged_gdf.geometry.area.sum():.10f}")
    print("\nPolygon type distribution:")
    print(merged_gdf['poly_type'].value_counts())
