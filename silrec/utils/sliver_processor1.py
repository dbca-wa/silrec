import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd
from shapely.ops import unary_union

class SliverProcessor:
    """
    A class to process and merge sliver polygons from intersection results.

    from silrec.utils.cookie_cut4 import PolygonIntersector
    intersector = PolygonIntersector(gdf1, gdf2)
    intersector.calculate_intersections(method='enhanced')
    result_gdf, gdf2_excl, combined_gdf, slivers_gdf = intersector.get_classified_results(
        sliver_threshold=5,
        include_pre_existing_slivers=False
    )
    result_gdf
    plot_multi([gdf1, gdf2, result_gdf, gdf2_excl, combined_gdf, slivers_gdf])

    plot_multi([combined_gdf, combined_gdf[combined_gdf.poly_type.isin(['CUT', 'HIST'])], combined_gdf[combined_gdf.poly_type=='HIST'], combined_gdf[combined_gdf.poly_type=='BASE'], combined_gdf[combined_gdf.poly_type=='CUT'], combined_gdf[combined_gdf.poly_type=='SLVR']])
    """

    def __init__(self, result_gdf, gdf2_excl, combined_gdf, slivers_gdf):
        """
        Initialize the SliverProcessor with classified intersection results.

        Parameters:
        -----------
        result_gdf : GeoDataFrame
            Intersection polygons with poly_type
        gdf2_excl : GeoDataFrame
            gdf2 polygons excluding intersection areas with poly_type
        combined_gdf : GeoDataFrame
            Combined GeoDataFrame with poly_type
        slivers_gdf : GeoDataFrame
            Sliver polygons only
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

    def _find_touching_neighbors(self, target_polygon, target_index, search_gdf):
        """
        Find polygons that touch the target polygon.

        Parameters:
        -----------
        target_polygon : shapely.geometry
            The polygon to find neighbors for
        target_index : any
            Index of the target polygon (to exclude from results)
        search_gdf : GeoDataFrame
            GeoDataFrame to search for neighbors in

        Returns:
        --------
        list
            List of indices of touching polygons
        """
        touching_indices = []

        for idx, row in search_gdf.iterrows():
            if idx == target_index:
                continue

            if target_polygon.touches(row.geometry) or target_polygon.intersects(row.geometry):
                touching_indices.append(idx)

        return touching_indices

    def _merge_polygons_by_ids(self, polygon_ids, original_gdf):
        """
        Merge specified polygons by their IDs.

        Parameters:
        -----------
        polygon_ids : list
            List of polygon indices to merge
        original_gdf : GeoDataFrame
            Original GeoDataFrame containing the polygons

        Returns:
        --------
        tuple (shapely.geometry, dict)
            Merged geometry and combined attributes
        """
        if len(polygon_ids) == 0:
            return None, {}

        # Get polygons to merge
        polygons_to_merge = original_gdf.loc[polygon_ids]

        # Merge geometries
        merged_geometry = unary_union(polygons_to_merge.geometry.tolist())

        # Combine attributes (take most common or first non-null value)
        combined_attrs = {}
        for col in polygons_to_merge.columns:
            if col == 'geometry':
                continue

            # For numeric columns, take mean
            if pd.api.types.is_numeric_dtype(polygons_to_merge[col]):
                combined_attrs[col] = polygons_to_merge[col].mean()
            else:
                # For categorical/string columns, take the most frequent value
                value_counts = polygons_to_merge[col].value_counts()
                if len(value_counts) > 0:
                    combined_attrs[col] = value_counts.index[0]
                else:
                    combined_attrs[col] = None

        # Update poly_type - if merging slivers with base, result should be base
        if 'poly_type' in combined_attrs:
            if 'SLVR' in polygons_to_merge['poly_type'].values and 'BASE' in polygons_to_merge['poly_type'].values:
                combined_attrs['poly_type'] = 'BASE'
            elif 'SLVR' in polygons_to_merge['poly_type'].values and 'CUT' in polygons_to_merge['poly_type'].values:
                combined_attrs['poly_type'] = 'CUT'
            elif 'SLVR' in polygons_to_merge['poly_type'].values and 'HIST' in polygons_to_merge['poly_type'].values:
                combined_attrs['poly_type'] = 'HIST'
            else:
                # Otherwise keep the most common poly_type
                poly_type_counts = polygons_to_merge['poly_type'].value_counts()
                combined_attrs['poly_type'] = poly_type_counts.index[0]

        combined_attrs['merged_from'] = f"merged_{len(polygon_ids)}_polygons"
        combined_attrs['original_ids'] = list(polygon_ids)

        return merged_geometry, combined_attrs

    def auto_merge_slivers_to_base(self):
        """
        Automatically merge SLVR polygons into their neighboring BASE polygons.

        Returns:
        --------
        GeoDataFrame
            New combined_gdf with slivers merged into BASE polygons
        """
        print("Starting auto-merge of slivers to BASE polygons...")

        # Create working copy
        working_gdf = self.combined_gdf.copy()
        sliver_mask = working_gdf['poly_type'] == 'SLVR'
        base_mask = working_gdf['poly_type'] == 'BASE'

        slivers_count = sliver_mask.sum()
        print(f"Found {slivers_count} SLVR polygons to process")

        if slivers_count == 0:
            print("No SLVR polygons found to merge.")
            return working_gdf

        # Track merged polygons
        merged_slivers = set()
        merge_operations = []

        # Process each sliver
        for sliver_idx in working_gdf[sliver_mask].index:
            if sliver_idx in merged_slivers:
                continue

            sliver_poly = working_gdf.loc[sliver_idx, 'geometry']

            # Find touching BASE polygons
            base_neighbors = self._find_touching_neighbors(
                sliver_poly, sliver_idx, working_gdf[base_mask]
            )

            if base_neighbors:
                # Merge sliver with its BASE neighbors
                polygons_to_merge = [sliver_idx] + base_neighbors
                merged_geometry, combined_attrs = self._merge_polygons_by_ids(
                    polygons_to_merge, working_gdf
                )

                if merged_geometry and merged_geometry.geom_type in ['Polygon', 'MultiPolygon']:
                    merge_operations.append({
                        'remove_indices': polygons_to_merge,
                        'new_geometry': merged_geometry,
                        'new_attributes': combined_attrs
                    })

                    # Mark these polygons as processed
                    merged_slivers.add(sliver_idx)
                    merged_slivers.update(base_neighbors)
                    print(f"  Merged SLVR {sliver_idx} with BASE neighbors {base_neighbors}")

        # Apply merge operations
        if merge_operations:
            # Remove merged polygons
            indices_to_remove = set()
            new_rows = []

            for op in merge_operations:
                indices_to_remove.update(op['remove_indices'])

                # Create new row for merged polygon
                new_row = op['new_attributes'].copy()
                new_row['geometry'] = op['new_geometry']
                new_rows.append(new_row)

            # Remove old polygons and add new merged ones
            result_gdf = working_gdf[~working_gdf.index.isin(indices_to_remove)].copy()
            new_gdf = gpd.GeoDataFrame(new_rows, crs=self.original_crs)
            result_gdf = pd.concat([result_gdf, new_gdf], ignore_index=True)

            print(f"Successfully merged {len(merged_slivers)} SLVR polygons into BASE polygons")
            print(f"Polygon count reduced from {len(working_gdf)} to {len(result_gdf)}")

            # Verify area preservation
            original_area = working_gdf.geometry.area.sum()
            new_area = result_gdf.geometry.area.sum()
            area_diff = abs(original_area - new_area)

            print(f"Area preservation check:")
            print(f"  Original area: {original_area:.6f}")
            print(f"  New area: {new_area:.6f}")
            print(f"  Difference: {area_diff:.10f} ({area_diff/original_area*100:.6f}%)")

            if area_diff/original_area > 0.0001:  # 0.01% tolerance
                print("  WARNING: Significant area change detected!")

            return result_gdf
        else:
            print("No suitable BASE neighbors found for SLVR polygons.")
            return working_gdf

    def merge_polygons_by_id(self, polygon_ids):
        """
        Merge specified polygons by their IDs.

        Parameters:
        -----------
        polygon_ids : list
            List of polygon indices to merge

        Returns:
        --------
        GeoDataFrame
            New combined_gdf with specified polygons merged
        """
        print(f"Attempting to merge polygons with IDs: {polygon_ids}")

        # Validate input IDs
        valid_ids = set(self.combined_gdf.index)
        invalid_ids = set(polygon_ids) - valid_ids

        if invalid_ids:
            raise ValueError(f"Invalid polygon IDs: {invalid_ids}")

        if len(polygon_ids) < 2:
            raise ValueError("At least 2 polygon IDs required for merging")

        # Check if polygons are touching
        polygons_subset = self.combined_gdf.loc[polygon_ids]
        all_touching = self._check_all_touching(polygons_subset)

        if not all_touching:
            raise ValueError("Not all specified polygons are touching. Cannot merge non-adjacent polygons.")

        # Create working copy
        working_gdf = self.combined_gdf.copy()

        # Merge the specified polygons
        merged_geometry, combined_attrs = self._merge_polygons_by_ids(polygon_ids, working_gdf)

        if not merged_geometry:
            raise ValueError("Failed to merge polygons")

        # Remove old polygons and add new merged one
        result_gdf = working_gdf[~working_gdf.index.isin(polygon_ids)].copy()

        new_row = combined_attrs.copy()
        new_row['geometry'] = merged_geometry
        new_gdf = gpd.GeoDataFrame([new_row], crs=self.original_crs)

        result_gdf = pd.concat([result_gdf, new_gdf], ignore_index=True)

        print(f"Successfully merged {len(polygon_ids)} polygons")
        print(f"Polygon count reduced from {len(working_gdf)} to {len(result_gdf)}")

        # Verify area preservation
        original_area = working_gdf.geometry.area.sum()
        new_area = result_gdf.geometry.area.sum()
        area_diff = abs(original_area - new_area)

        print(f"Area preservation check:")
        print(f"  Original area: {original_area:.6f}")
        print(f"  New area: {new_area:.6f}")
        print(f"  Difference: {area_diff:.10f} ({area_diff/original_area*100:.6f}%)")

        return result_gdf

    def _check_all_touching(self, polygons_gdf):
        """
        Check if all polygons in the subset are touching (directly or indirectly).

        Parameters:
        -----------
        polygons_gdf : GeoDataFrame
            Subset of polygons to check

        Returns:
        --------
        bool
            True if all polygons are connected
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

    def get_sliver_statistics(self):
        """
        Get statistics about sliver polygons.

        Returns:
        --------
        dict
            Dictionary containing sliver statistics
        """
        sliver_mask = self.combined_gdf['poly_type'] == 'SLVR'
        slivers = self.combined_gdf[sliver_mask]

        stats = {
            'total_slivers': len(slivers),
            'sliver_area_total': slivers.geometry.area.sum() if len(slivers) > 0 else 0,
            'sliver_area_min': slivers.geometry.area.min() if len(slivers) > 0 else 0,
            'sliver_area_max': slivers.geometry.area.max() if len(slivers) > 0 else 0,
            'sliver_area_mean': slivers.geometry.area.mean() if len(slivers) > 0 else 0,
            'sliver_neighbors_info': {}
        }

        # Analyze neighbors for each sliver
        for idx, sliver in slivers.iterrows():
            neighbors = self._find_touching_neighbors(
                sliver.geometry, idx, self.combined_gdf
            )
            neighbor_types = self.combined_gdf.loc[neighbors, 'poly_type'].value_counts().to_dict()

            stats['sliver_neighbors_info'][idx] = {
                'area': sliver.geometry.area,
                'perimeter': sliver.geometry.length,
                'neighbor_count': len(neighbors),
                'neighbor_types': neighbor_types
            }

        return stats

    def suggest_sliver_merges(self):
        """
        Suggest optimal sliver merge operations.

        Returns:
        --------
        dict
            Dictionary with merge suggestions
        """
        sliver_mask = self.combined_gdf['poly_type'] == 'SLVR'
        slivers = self.combined_gdf[sliver_mask]

        suggestions = {}

        for idx, sliver in slivers.iterrows():
            neighbors = self._find_touching_neighbors(
                sliver.geometry, idx, self.combined_gdf
            )

            neighbor_types = self.combined_gdf.loc[neighbors, 'poly_type']

            # Prefer merging with BASE, then CUT, then HIST
            best_neighbor_type = None
            best_neighbors = []

            for poly_type in ['BASE', 'CUT', 'HIST']:
                type_neighbors = neighbor_types[neighbor_types == poly_type].index.tolist()
                if type_neighbors:
                    best_neighbor_type = poly_type
                    best_neighbors = type_neighbors
                    break

            suggestions[idx] = {
                'sliver_area': sliver.geometry.area,
                'recommended_action': f'Merge with {best_neighbor_type}' if best_neighbor_type else 'No suitable neighbors',
                'neighbors_to_merge': [idx] + best_neighbors if best_neighbor_type else [],
                'target_poly_type': best_neighbor_type
            }

        return suggestions


# Example usage:
if __name__ == "__main__":
    # First, create intersection results using the first class
    from shapely.geometry import Polygon

    # Create sample data
    poly1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
    gdf1 = gpd.GeoDataFrame({'id': [1], 'name': ['main_polygon']},
                           geometry=[poly1], crs='EPSG:4326')

    # Create gdf2 with polygons that will produce slivers
    polygons2 = [
        Polygon([(1, 1), (4, 1), (4, 4), (1, 4)]),
        Polygon([(2, 0), (5, 0), (5, 2), (2, 2)]),
        Polygon([(0, 2), (2, 2), (2, 5), (0, 5)]),
        Polygon([(4, 4), (6, 4), (6, 6), (4, 6)]),
        # Add some small sliver-like polygons
        Polygon([(2.9, 2.9), (3.0, 2.9), (3.0, 3.0), (2.9, 3.0)]),  # Small square
        Polygon([(1.5, 2.9), (1.6, 2.9), (1.6, 3.1), (1.5, 3.1)]),  # Thin rectangle
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
        sliver_threshold=0.5,  # Low threshold to identify more slivers
        include_pre_existing_slivers=False
    )

    print("=== Initial Results ===")
    print(f"Total polygons: {len(combined_gdf)}")
    print(f"SLVR polygons: {len(slivers_gdf)}")
    print("Poly type distribution:")
    print(combined_gdf['poly_type'].value_counts())

    # Now use the SliverProcessor
    print("\n=== Using SliverProcessor ===")
    processor = SliverProcessor(result_gdf, gdf2_excl, combined_gdf, slivers_gdf)

    # Get statistics
    stats = processor.get_sliver_statistics()
    print(f"Sliver statistics: {stats['total_slivers']} slivers found")

    # Get merge suggestions
    suggestions = processor.suggest_sliver_merges()
    print("\nMerge suggestions:")
    for sliver_id, suggestion in suggestions.items():
        print(f"  Sliver {sliver_id}: {suggestion['recommended_action']}")

    # Auto-merge slivers to BASE polygons
    print("\n=== Auto-merging slivers to BASE polygons ===")
    merged_gdf = processor.auto_merge_slivers_to_base()

    print(f"\nAfter auto-merge:")
    print(f"Total polygons: {len(merged_gdf)}")
    if 'poly_type' in merged_gdf.columns:
        print("Poly type distribution:")
        print(merged_gdf['poly_type'].value_counts())

    # Manual merge by ID
    print("\n=== Manual merge by ID ===")
    # Get some polygon IDs that are touching (you would normally select these based on your data)
    sample_polygons = merged_gdf.head(3)
    if len(sample_polygons) >= 2:
        # Check if first two polygons are touching
        poly1 = sample_polygons.iloc[0].geometry
        poly2 = sample_polygons.iloc[1].geometry

        if poly1.touches(poly2) or poly1.intersects(poly2):
            poly_ids = [sample_polygons.index[0], sample_polygons.index[1]]
            try:
                manually_merged_gdf = processor.merge_polygons_by_id(poly_ids)
                print(f"Manual merge successful! Reduced to {len(manually_merged_gdf)} polygons")
            except ValueError as e:
                print(f"Manual merge failed: {e}")
