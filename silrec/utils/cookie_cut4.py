import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd

class PolygonIntersector:
    """
    A class to handle polygon intersections between two GeoDataFrames.

    from silrec.utils.cookie_cut4 import PolygonIntersector
    intersector = PolygonIntersector(gdf1, gdf2)
    intersector.calculate_intersections(method='enhanced')
    result_gdf, gdf2_excl, combined_gdf, slivers_gdf = intersector.get_classified_results(
        sliver_threshold=5,
        include_pre_existing_slivers=False
    )
    result_gdf
    plot_multi([gdf1, gdf2, result_gdf, gdf2_excl, combined_gdf, slivers_gdf])

    plot_multi([combined_gdf, combined_gdf[combined_gdf.poly_type=='HIST'], combined_gdf[combined_gdf.poly_type=='BASE'], combined_gdf[combined_gdf.poly_type=='CUT'], combined_gdf[combined_gdf.poly_type=='SLVR']])
    """

    def __init__(self, gdf1, gdf2):
        """
        Initialize the PolygonIntersector with two GeoDataFrames.

        Parameters:
        -----------
        gdf1 : GeoDataFrame
            GeoDataFrame containing exactly one polygon geometry
        gdf2 : GeoDataFrame
            GeoDataFrame containing multiple polygon geometries
        """
        self.gdf1 = gdf1.copy()
        self.gdf2 = gdf2.copy()
        self.result_gdf = None
        self.gdf2_excl = None
        self.combined_gdf = None
        self._validate_input()

    def _validate_input(self):
        """Validate input GeoDataFrames."""
        if len(self.gdf1) != 1:
            raise ValueError("gdf1 must contain exactly one polygon")

        if len(self.gdf2) == 0:
            raise ValueError("gdf2 must contain at least one polygon")

        if not all(self.gdf1.geometry.type.isin(['Polygon', 'MultiPolygon'])):
            raise ValueError("gdf1 must contain only polygon geometries")

        if not all(self.gdf2.geometry.type.isin(['Polygon', 'MultiPolygon'])):
            raise ValueError("gdf2 must contain only polygon geometries")

    def calculate_intersections(self, method='enhanced'):
        """
        Calculate intersections between gdf1 and gdf2.

        Parameters:
        -----------
        method : str
            Method to use for intersection calculation:
            - 'enhanced': Uses geometric difference for precise results
            - 'basic': Simple intersection without difference calculation
            - 'overlay': Uses geopandas overlay function

        Returns:
        --------
        self
        """
        if method == 'enhanced':
            self._calculate_enhanced_intersections()
        elif method == 'basic':
            self._calculate_basic_intersections()
        elif method == 'overlay':
            self._calculate_overlay_intersections()
        else:
            raise ValueError("Method must be 'enhanced', 'basic', or 'overlay'")

        # Create combined dataframe and classify polygons
        self._create_combined_gdf()
        self._classify_polygons()

        return self

    def _calculate_enhanced_intersections(self):
        """Calculate intersections using enhanced method with geometric differences."""
        main_polygon = self.gdf1.geometry.iloc[0]
        intersections = []
        updated_gdf2_rows = []

        for idx, row in self.gdf2.iterrows():
            poly2 = row.geometry

            if main_polygon.intersects(poly2):
                intersection = main_polygon.intersection(poly2)
                difference = poly2.difference(main_polygon)

                # Handle intersection
                if not intersection.is_empty:
                    self._add_intersection_geometries(intersection, row, intersections, 'intersection')

                # Handle difference (non-intersecting part)
                if not difference.is_empty:
                    self._add_difference_geometries(difference, row, updated_gdf2_rows, 'cut')
            else:
                # No intersection, keep original polygon
                original_row = row.copy()
                original_row['geometry_type'] = 'original'
                updated_gdf2_rows.append(original_row)

        self._create_result_dataframes(intersections, updated_gdf2_rows)

    def _calculate_basic_intersections(self):
        """Calculate intersections using basic method (exclude entire intersecting polygons)."""
        main_polygon = self.gdf1.geometry.iloc[0]
        intersections = []
        intersecting_indices = set()

        for idx, row in self.gdf2.iterrows():
            poly2 = row.geometry

            if main_polygon.intersects(poly2):
                intersection = main_polygon.intersection(poly2)

                if not intersection.is_empty:
                    self._add_intersection_geometries(intersection, row, intersections, 'intersection')
                    intersecting_indices.add(idx)

        if intersections:
            self.result_gdf = gpd.GeoDataFrame(intersections, crs=self.gdf2.crs)
            self.result_gdf['source_gdf1_id'] = self.gdf1.index[0]
            self.gdf2_excl = self.gdf2[~self.gdf2.index.isin(intersecting_indices)].copy()
            self.gdf2_excl['geometry_type'] = 'original'
        else:
            self.result_gdf = gpd.GeoDataFrame(columns=self.gdf2.columns.tolist() + ['source_gdf1_id'],
                                             crs=self.gdf2.crs)
            self.gdf2_excl = self.gdf2.copy()
            self.gdf2_excl['geometry_type'] = 'original'

    def _calculate_overlay_intersections(self):
        """Calculate intersections using geopandas overlay."""
        gdf1_with_id = self.gdf1.copy()
        gdf2_with_id = self.gdf2.copy()
        gdf1_with_id['gdf1_id'] = self.gdf1.index[0]
        gdf2_with_id['gdf2_id'] = self.gdf2.index

        result = gpd.overlay(gdf1_with_id, gdf2_with_id, how='intersection', keep_geom_type=True)

        if not result.empty and 'gdf2_id' in result.columns:
            intersecting_indices = result['gdf2_id'].unique()
            self.gdf2_excl = self.gdf2[~self.gdf2.index.isin(intersecting_indices)].copy()
            self.gdf2_excl['geometry_type'] = 'original'
        else:
            self.gdf2_excl = self.gdf2.copy()
            self.gdf2_excl['geometry_type'] = 'original'

        self.result_gdf = result
        self.result_gdf['geometry_type'] = 'intersection'

    def _add_intersection_geometries(self, intersection, original_row, intersections_list, geom_type):
        """Add intersection geometries to the results list."""
        if intersection.geom_type == 'Polygon':
            new_row = original_row.copy()
            new_row['geometry'] = intersection
            new_row['geometry_type'] = geom_type
            intersections_list.append(new_row)
        elif intersection.geom_type == 'MultiPolygon':
            for poly in intersection.geoms:
                new_row = original_row.copy()
                new_row['geometry'] = poly
                new_row['geometry_type'] = geom_type
                intersections_list.append(new_row)
        elif intersection.geom_type == 'GeometryCollection':
            for geom in intersection.geoms:
                if geom.geom_type == 'Polygon':
                    new_row = original_row.copy()
                    new_row['geometry'] = geom
                    new_row['geometry_type'] = geom_type
                    intersections_list.append(new_row)

    def _add_difference_geometries(self, difference, original_row, differences_list, geom_type):
        """Add difference geometries to the results list."""
        if difference.geom_type == 'Polygon':
            updated_row = original_row.copy()
            updated_row['geometry'] = difference
            updated_row['geometry_type'] = geom_type
            differences_list.append(updated_row)
        elif difference.geom_type == 'MultiPolygon':
            for poly in difference.geoms:
                updated_row = original_row.copy()
                updated_row['geometry'] = poly
                updated_row['geometry_type'] = geom_type
                differences_list.append(updated_row)

    def _create_result_dataframes(self, intersections, updated_gdf2_rows):
        """Create the result dataframes from intersection and difference lists."""
        if intersections:
            self.result_gdf = gpd.GeoDataFrame(intersections, crs=self.gdf2.crs)
            self.result_gdf['source_gdf1_id'] = self.gdf1.index[0]
        else:
            self.result_gdf = gpd.GeoDataFrame(columns=self.gdf2.columns.tolist() + ['source_gdf1_id'],
                                             crs=self.gdf2.crs)

        if updated_gdf2_rows:
            self.gdf2_excl = gpd.GeoDataFrame(updated_gdf2_rows, crs=self.gdf2.crs)
        else:
            self.gdf2_excl = gpd.GeoDataFrame(columns=self.gdf2.columns.tolist(), crs=self.gdf2.crs)

    def _create_combined_gdf(self):
        """Create combined GeoDataFrame with all polygons."""
        if self.result_gdf is None or self.gdf2_excl is None:
            raise ValueError("Please call calculate_intersections() first")

        # Ensure both dataframes have the same columns
        result_cols = set(self.result_gdf.columns)
        excl_cols = set(self.gdf2_excl.columns)

        # Add missing columns to each dataframe
        for col in excl_cols - result_cols:
            self.result_gdf[col] = None

        for col in result_cols - excl_cols:
            self.gdf2_excl[col] = None

        # Combine the dataframes
        combined_gdf = pd.concat([self.result_gdf, self.gdf2_excl],
                                ignore_index=True, sort=False)

        # Reset the geometry column to be active
        self.combined_gdf = gpd.GeoDataFrame(combined_gdf, geometry='geometry', crs=self.gdf2.crs)

    def _classify_polygons(self):
        """Classify polygons into HIST, CUT, BASE, and SLVR types."""
        if self.combined_gdf is None:
            raise ValueError("Combined GeoDataFrame not created")

        # Initialize all as HIST (will be updated)
        self.combined_gdf['poly_type'] = 'HIST'

        # Identify CUT polygons (modified by intersection but not covered by gdf1)
        cut_mask = self.combined_gdf['geometry_type'] == 'cut'
        self.combined_gdf.loc[cut_mask, 'poly_type'] = 'CUT'

        # Identify BASE polygons (covered by gdf1, excluding intersections that will be SLVR)
        base_mask = self.combined_gdf['geometry_type'] == 'intersection'
        self.combined_gdf.loc[base_mask, 'poly_type'] = 'BASE'

        # Update result_gdf and gdf2_excl with poly_type
        if len(self.result_gdf) > 0:
            result_mask = self.combined_gdf['geometry_type'] == 'intersection'
            self.result_gdf = self.combined_gdf[result_mask].copy()

        if len(self.gdf2_excl) > 0:
            excl_mask = self.combined_gdf['geometry_type'].isin(['original', 'cut'])
            self.gdf2_excl = self.combined_gdf[excl_mask].copy()

    def identify_slivers(self, threshold=5, include_pre_existing=False):
        """
        Identify land slivers based on area-to-perimeter ratio.

        Parameters:
        -----------
        threshold : float
            Maximum area-to-perimeter ratio for sliver classification
        include_pre_existing : bool
            If True, include pre-existing slivers from original gdf2

        Returns:
        --------
        GeoDataFrame
            Sliver polygons only
        """
        if self.combined_gdf is None:
            raise ValueError("Please call calculate_intersections() first")

        # Calculate area and perimeter
        gdf = self.combined_gdf.copy()
        gdf['area'] = gdf.geometry.area
        gdf['perimeter'] = gdf.geometry.length
        gdf['area_perimeter_ratio'] = gdf['area'] / gdf['perimeter']

        # Create mask for slivers
        sliver_mask = gdf['area_perimeter_ratio'] < threshold

        if not include_pre_existing:
            # Only include slivers that were created by the intersection
            intersection_created = gdf['geometry_type'].isin(['intersection', 'cut'])
            sliver_mask = sliver_mask & intersection_created

        slivers_gdf = gdf[sliver_mask].copy()

        # Update poly_type for slivers in the main combined_gdf
        sliver_indices = slivers_gdf.index
        self.combined_gdf.loc[sliver_indices, 'poly_type'] = 'SLVR'

        # Also update result_gdf and gdf2_excl if slivers are found in those
        if len(self.result_gdf) > 0:
            result_sliver_mask = self.result_gdf.index.isin(sliver_indices)
            self.result_gdf.loc[result_sliver_mask, 'poly_type'] = 'SLVR'

        if len(self.gdf2_excl) > 0:
            excl_sliver_mask = self.gdf2_excl.index.isin(sliver_indices)
            self.gdf2_excl.loc[excl_sliver_mask, 'poly_type'] = 'SLVR'

        return slivers_gdf

    def get_intersections(self):
        """
        Get the intersection results.

        Returns:
        --------
        tuple (GeoDataFrame, GeoDataFrame)
            result_gdf: Intersection polygons
            gdf2_excl: gdf2 polygons excluding intersection areas
        """
        if self.result_gdf is None or self.gdf2_excl is None:
            raise ValueError("Please call calculate_intersections() first")

        return self.result_gdf, self.gdf2_excl

    def get_combined_gdf(self):
        """
        Get a combined GeoDataFrame with both intersection and remaining polygons.

        Returns:
        --------
        GeoDataFrame
            Combined GeoDataFrame with all polygons and their types
        """
        if self.combined_gdf is None:
            raise ValueError("Please call calculate_intersections() first")

        return self.combined_gdf

    def get_all_results(self):
        """
        Get all results in one method call.

        Returns:
        --------
        tuple (GeoDataFrame, GeoDataFrame, GeoDataFrame)
            result_gdf: Intersection polygons
            gdf2_excl: gdf2 polygons excluding intersection areas
            combined_gdf: Combined GeoDataFrame with all polygons
        """
        result_gdf, gdf2_excl = self.get_intersections()
        combined_gdf = self.get_combined_gdf()

        return result_gdf, gdf2_excl, combined_gdf

    def get_classified_results(self, sliver_threshold=5, include_pre_existing_slivers=False):
        """
        Get fully classified results including sliver identification.

        Parameters:
        -----------
        sliver_threshold : float
            Maximum area-to-perimeter ratio for sliver classification
        include_pre_existing_slivers : bool
            If True, include pre-existing slivers from original gdf2

        Returns:
        --------
        tuple (GeoDataFrame, GeoDataFrame, GeoDataFrame, GeoDataFrame)
            result_gdf: Intersection polygons with poly_type
            gdf2_excl: gdf2 polygons excluding intersection areas with poly_type
            combined_gdf: Combined GeoDataFrame with poly_type
            slivers_gdf: Sliver polygons only
        """
        # Identify slivers
        slivers_gdf = self.identify_slivers(threshold=sliver_threshold,
                                          include_pre_existing=include_pre_existing_slivers)

        return self.result_gdf, self.gdf2_excl, self.combined_gdf, slivers_gdf

    def summary(self):
        """Print a summary of the intersection results."""
        if self.combined_gdf is None:
            print("No results calculated. Call calculate_intersections() first.")
            return

        print("=== Polygon Intersection Summary ===")
        print(f"Original gdf1 polygons: {len(self.gdf1)}")
        print(f"Original gdf2 polygons: {len(self.gdf2)}")
        print(f"Intersection polygons: {len(self.result_gdf)}")
        print(f"Remaining gdf2 polygons: {len(self.gdf2_excl)}")
        print(f"Combined total polygons: {len(self.combined_gdf)}")

        if 'poly_type' in self.combined_gdf.columns:
            poly_type_counts = self.combined_gdf['poly_type'].value_counts()
            print("\nPolygon Type Distribution:")
            for poly_type, count in poly_type_counts.items():
                print(f"  {poly_type}: {count} polygons")

        if len(self.result_gdf) > 0:
            print(f"Intersection area: {self.result_gdf.geometry.area.sum():.4f}")
        if len(self.gdf2_excl) > 0:
            print(f"Remaining area: {self.gdf2_excl.geometry.area.sum():.4f}")


# Example usage:
if __name__ == "__main__":
    # Create sample data
    from shapely.geometry import Polygon

    # gdf1 with one polygon
    poly1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
    gdf1 = gpd.GeoDataFrame({'id': [1], 'name': ['main_polygon']},
                           geometry=[poly1], crs='EPSG:4326')

    # gdf2 with multiple polygons (including some that might create slivers)
    polygons2 = [
        Polygon([(1, 1), (4, 1), (4, 4), (1, 4)]),  # Will intersect
        Polygon([(2, 0), (5, 0), (5, 2), (2, 2)]),  # Will intersect
        Polygon([(0, 2), (2, 2), (2, 5), (0, 5)]),  # Will intersect
        Polygon([(4, 4), (6, 4), (6, 6), (4, 6)]),  # Will NOT intersect
        # Add a small polygon that might be a sliver
        Polygon([(2.9, 2.9), (3.1, 2.9), (3.1, 3.1), (2.9, 3.1)])  # Small square
    ]
    gdf2 = gpd.GeoDataFrame({
        'id': [10, 20, 30, 40, 50],
        'type': ['A', 'B', 'C', 'D', 'E'],
        'value': [100, 200, 300, 400, 500]
    }, geometry=polygons2, crs='EPSG:4326')

    # Create intersector instance
    intersector = PolygonIntersector(gdf1, gdf2)

    # Calculate intersections
    intersector.calculate_intersections(method='enhanced')

    # Get classified results with sliver identification
    print("=== Classified Results with Slivers ===")
    result_gdf, gdf2_excl, combined_gdf, slivers_gdf = intersector.get_classified_results(
        sliver_threshold=5,
        include_pre_existing_slivers=False
    )

    print(f"Total slivers identified: {len(slivers_gdf)}")
    print(f"Sliver details:")
    if len(slivers_gdf) > 0:
        for idx, row in slivers_gdf.iterrows():
            print(f"  - ID: {row['id']}, Area: {row.geometry.area:.4f}, "
                  f"Ratio: {row['area_perimeter_ratio']:.4f}")

    print(f"\nCombined GDF poly_type distribution:")
    print(combined_gdf['poly_type'].value_counts())

    print(f"\nResult GDF poly_type distribution:")
    if 'poly_type' in result_gdf.columns:
        print(result_gdf['poly_type'].value_counts())

    print(f"\nGDF2 excl poly_type distribution:")
    if 'poly_type' in gdf2_excl.columns:
        print(gdf2_excl['poly_type'].value_counts())

    print("\n=== Summary ===")
    intersector.summary()

    # Test with different sliver threshold
    print("\n" + "="*50)
    print("Testing with different sliver threshold (threshold=0.1):")
    result_gdf2, gdf2_excl2, combined_gdf2, slivers_gdf2 = intersector.get_classified_results(
        sliver_threshold=0.1,
        include_pre_existing_slivers=False
    )
    print(f"Slivers with threshold 0.1: {len(slivers_gdf2)}")
