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

        # Store original indices for reference
        self.original_indices = combined_gdf.index.tolist()

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

    def merge_polygons_by_id(self, polygon_ids, area_tolerance=0.001):
        """
        Merge specified polygons by their IDs.

        Parameters:
        -----------
        polygon_ids : list
            List of polygon indices (from the original combined_gdf) to merge
        area_tolerance : float
            Maximum allowed area difference as fraction of total area

        Returns:
        --------
        GeoDataFrame
            New combined_gdf with specified polygons merged
        """
        print(f"Attempting to merge polygons with IDs: {polygon_ids}")

        # Create working copy - keep original indices for reference
        working_gdf = self.combined_gdf.copy()
        original_area = working_gdf.geometry.area.sum()

        # Validate input IDs
        valid_ids = set(working_gdf.index)
        invalid_ids = set(polygon_ids) - valid_ids

        if invalid_ids:
            raise ValueError(f"Invalid polygon IDs: {invalid_ids}. Valid IDs are: {list(valid_ids)[:10]}...")

        if len(polygon_ids) < 2:
            raise ValueError("At least 2 polygon IDs required for merging")

        print(f"Validated {len(polygon_ids)} polygon IDs for merging")

        # Check if polygons are touching
        polygons_subset = working_gdf.loc[polygon_ids]
        print(f"Polygons to merge: {len(polygons_subset)}")

        all_touching = self._check_all_touching(polygons_subset)

        if not all_touching:
            # Provide more detailed information about which polygons aren't touching
            non_touching_pairs = self._find_non_touching_pairs(polygons_subset)
            error_msg = f"Not all specified polygons are touching. Cannot merge non-adjacent polygons.\n"
            error_msg += f"Non-touching pairs: {non_touching_pairs}"
            raise ValueError(error_msg)

        print("All polygons are touching - proceeding with merge...")

        # Merge the specified polygons
        try:
            merged_geometry, combined_attrs = self._merge_polygons_by_ids(polygon_ids, working_gdf)

            if not merged_geometry:
                raise ValueError("Merge operation returned no geometry")

            if not merged_geometry.is_valid:
                print("Attempting to fix invalid geometry...")
                merged_geometry = merged_geometry.buffer(0)  # Try to fix validity
                if not merged_geometry.is_valid:
                    raise ValueError("Merged geometry is invalid and could not be fixed")

            # Verify area preservation for this specific merge
            original_merged_area = working_gdf.loc[polygon_ids].geometry.area.sum()
            new_merged_area = merged_geometry.area
            area_diff = abs(original_merged_area - new_merged_area)
            area_diff_percent = (area_diff / original_merged_area * 100) if original_merged_area > 0 else 0

            print(f"Area check - Original: {original_merged_area:.6f}, New: {new_merged_area:.6f}, Diff: {area_diff_percent:.4f}%")

            if area_diff_percent > area_tolerance * 100:
                raise ValueError(f"Area preservation check failed: {area_diff_percent:.4f}% difference (tolerance: {area_tolerance * 100}%)")

            # Remove old polygons and add new merged one
            result_gdf = working_gdf[~working_gdf.index.isin(polygon_ids)].copy()

            # Create new row for merged polygon
            new_row = combined_attrs.copy()
            new_row['geometry'] = merged_geometry

            # Ensure all required columns are present
            for col in result_gdf.columns:
                if col not in new_row and col != 'geometry':
                    new_row[col] = None

            # Create new GeoDataFrame for the merged polygon
            new_gdf = gpd.GeoDataFrame([new_row], crs=self.original_crs)

            # Combine with the remaining polygons
            result_gdf = pd.concat([result_gdf, new_gdf], ignore_index=False)

            # Final area check
            new_total_area = result_gdf.geometry.area.sum()
            total_area_diff = abs(original_area - new_total_area)
            total_area_diff_percent = (total_area_diff / original_area * 100) if original_area > 0 else 0

            print(f"\nMerge successful!")
            print(f"  Original polygon count: {len(working_gdf)}")
            print(f"  New polygon count: {len(result_gdf)}")
            print(f"  Polygons removed: {len(polygon_ids)}")
            print(f"  Polygons added: 1")
            print(f"  Merged area - original: {original_merged_area:.6f}, new: {new_merged_area:.6f}")
            print(f"  Total area - original: {original_area:.6f}, new: {new_total_area:.6f}")
            print(f"  Total area difference: {total_area_diff:.8f} ({total_area_diff_percent:.6f}%)")

            if total_area_diff_percent > area_tolerance * 100:
                print("  WARNING: Significant total area change detected!")

            return result_gdf

        except Exception as e:
            print(f"Merge failed with error: {str(e)}")
            raise

    def _find_non_touching_pairs(self, polygons_gdf):
        """
        Find pairs of polygons that are not touching.
        """
        non_touching_pairs = []
        indices = list(polygons_gdf.index)

        for i, idx1 in enumerate(indices):
            poly1 = polygons_gdf.loc[idx1, 'geometry']
            for j, idx2 in enumerate(indices[i+1:], i+1):
                poly2 = polygons_gdf.loc[idx2, 'geometry']
                if not poly1.touches(poly2) and not poly1.intersects(poly2):
                    non_touching_pairs.append((idx1, idx2))

        return non_touching_pairs

    def _check_all_touching(self, polygons_gdf):
        """
        Check if all polygons in the subset are touching (directly or indirectly).
        """
        if len(polygons_gdf) < 2:
            return True

        # Create adjacency graph
        graph = {}
        indices = list(polygons_gdf.index)

        for i, idx1 in enumerate(indices):
            graph[idx1] = []
            poly1 = polygons_gdf.loc[idx1, 'geometry']

            for j, idx2 in enumerate(indices):
                if i == j:
                    continue

                poly2 = polygons_gdf.loc[idx2, 'geometry']
                if poly1.touches(poly2) or poly1.intersects(poly2):
                    graph[idx1].append(idx2)

        # Check connectivity using BFS
        visited = set()
        queue = [indices[0]]

        while queue:
            current = queue.pop(0)
            if current not in visited:
                visited.add(current)
                queue.extend([n for n in graph[current] if n not in visited])

        return len(visited) == len(indices)

    def _merge_polygons_by_ids(self, polygon_ids, original_gdf):
        """
        Merge specified polygons by their IDs.
        """
        if len(polygon_ids) == 0:
            return None, {}

        # Get polygons to merge
        polygons_to_merge = original_gdf.loc[polygon_ids]
        print(f"  Merging {len(polygons_to_merge)} polygons...")

        # Merge geometries using unary_union
        try:
            geometry_list = polygons_to_merge.geometry.tolist()
            merged_geometry = unary_union(geometry_list)

            # Handle different geometry types that might result
            if merged_geometry.is_empty:
                raise ValueError("Merge resulted in empty geometry")

            if merged_geometry.geom_type == 'MultiPolygon':
                # For MultiPolygon, we have options:
                # Option 1: Use the largest polygon
                areas = [poly.area for poly in merged_geometry.geoms]
                largest_idx = np.argmax(areas)
                merged_geometry = merged_geometry.geoms[largest_idx]
                print(f"    MultiPolygon result - using largest component (area: {merged_geometry.area:.6f})")

            elif merged_geometry.geom_type not in ['Polygon', 'MultiPolygon']:
                raise ValueError(f"Unexpected geometry type after merge: {merged_geometry.geom_type}")

            # Ensure the geometry is valid
            if not merged_geometry.is_valid:
                print("    Fixing invalid geometry with buffer(0)...")
                merged_geometry = merged_geometry.buffer(0)
                if not merged_geometry.is_valid:
                    raise ValueError("Could not fix invalid geometry")

        except Exception as e:
            print(f"    Geometry merge error: {e}")
            # Fallback: use convex hull
            print("    Using convex hull as fallback...")
            geometry_list = polygons_to_merge.geometry.tolist()
            merged_geometry = unary_union(geometry_list).convex_hull

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

    # ... (keep the other methods from previous implementation unchanged)
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

    def auto_merge_all_slivers(self, area_tolerance=0.001):
        """
        Merge ALL SLVR polygons into their neighbors with preference for BASE polygons
        and longest shared boundaries.
        """
        # ... (keep the previous implementation of this method)
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
        # ... (keep the previous implementation of this method)
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


# Example usage to test the fixed merge_polygons_by_id method:
if __name__ == "__main__":
    # Create sample data
    from shapely.geometry import Polygon

    poly1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
    gdf1 = gpd.GeoDataFrame({'id': [1], 'name': ['main_polygon']},
                           geometry=[poly1], crs='EPSG:4326')

    # Create gdf2 with touching polygons that we can merge
    polygons2 = [
        Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),  # Polygon A
        Polygon([(2, 1), (3, 1), (3, 2), (2, 2)]),  # Polygon B - touches A
        Polygon([(1, 2), (2, 2), (2, 3), (1, 3)]),  # Polygon C - touches A
        Polygon([(4, 4), (5, 4), (5, 5), (4, 5)]),  # Polygon D - isolated
    ]
    gdf2 = gpd.GeoDataFrame({
        'id': [10, 20, 30, 40],
        'type': ['A', 'B', 'C', 'D'],
        'value': [100, 200, 300, 400]
    }, geometry=polygons2, crs='EPSG:4326')

    # Use first class to get intersection results
    intersector = PolygonIntersector(gdf1, gdf2)
    intersector.calculate_intersections(method='enhanced')
    result_gdf, gdf2_excl, combined_gdf, slivers_gdf = intersector.get_classified_results(
        sliver_threshold=0.1,
        include_pre_existing_slivers=False
    )

    print("=== Initial State ===")
    print(f"Total polygons: {len(combined_gdf)}")
    print("Polygon IDs:", combined_gdf.index.tolist())
    print("Polygon types:")
    print(combined_gdf['poly_type'].value_counts())

    # Use SliverProcessor
    processor = SliverProcessor(result_gdf, gdf2_excl, combined_gdf, slivers_gdf)

    # Test merge_polygons_by_id with touching polygons
    print("\n=== Testing merge_polygons_by_id ===")

    # Find two touching polygons to merge
    touching_found = False
    for i, poly1 in combined_gdf.iterrows():
        for j, poly2 in combined_gdf.iterrows():
            if i != j and poly1.geometry.touches(poly2.geometry):
                print(f"Found touching polygons: {i} and {j}")
                try:
                    merged_result = processor.merge_polygons_by_id([i, j])
                    print("SUCCESS: merge_polygons_by_id worked!")
                    print(f"Result has {len(merged_result)} polygons")
                    touching_found = True
                    break
                except Exception as e:
                    print(f"ERROR: {e}")
                break
        if touching_found:
            break

    if not touching_found:
        print("No touching polygons found to test merge_polygons_by_id")
