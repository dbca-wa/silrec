import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd

class PolygonIntersector:
    """
    A class to handle polygon intersections between two GeoDataFrames.

    from silrec.utils.cookie_cut3 import PolygonIntersector
    from silrec.utils.plot_utils import plot_multi, plot_gdf, plot_overlay

    intersector = PolygonIntersector(gdf1, gdf2)
    intersector.calculate_intersections(method='enhanced')
    result_gdf, gdf2_excl, combined_gdf = intersector.get_all_results()

    plot_multi([gdf1, gdf2, result_gdf, gdf2_excl, combined_gdf])
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
                    self._add_intersection_geometries(intersection, row, intersections)

                # Handle difference (non-intersecting part)
                if not difference.is_empty:
                    self._add_difference_geometries(difference, row, updated_gdf2_rows)
            else:
                # No intersection, keep original polygon
                updated_gdf2_rows.append(row.copy())

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
                    self._add_intersection_geometries(intersection, row, intersections)
                    intersecting_indices.add(idx)

        if intersections:
            self.result_gdf = gpd.GeoDataFrame(intersections, crs=self.gdf2.crs)
            self.result_gdf['source_gdf1_id'] = self.gdf1.index[0]
            self.gdf2_excl = self.gdf2[~self.gdf2.index.isin(intersecting_indices)].copy()
        else:
            self.result_gdf = gpd.GeoDataFrame(columns=self.gdf2.columns.tolist() + ['source_gdf1_id'],
                                             crs=self.gdf2.crs)
            self.gdf2_excl = self.gdf2.copy()

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
        else:
            self.gdf2_excl = self.gdf2.copy()

        self.result_gdf = result

    def _add_intersection_geometries(self, intersection, original_row, intersections_list):
        """Add intersection geometries to the results list."""
        if intersection.geom_type == 'Polygon':
            new_row = original_row.copy()
            new_row['geometry'] = intersection
            intersections_list.append(new_row)
        elif intersection.geom_type == 'MultiPolygon':
            for poly in intersection.geoms:
                new_row = original_row.copy()
                new_row['geometry'] = poly
                intersections_list.append(new_row)
        elif intersection.geom_type == 'GeometryCollection':
            for geom in intersection.geoms:
                if geom.geom_type == 'Polygon':
                    new_row = original_row.copy()
                    new_row['geometry'] = geom
                    intersections_list.append(new_row)

    def _add_difference_geometries(self, difference, original_row, differences_list):
        """Add difference geometries to the results list."""
        if difference.geom_type == 'Polygon':
            updated_row = original_row.copy()
            updated_row['geometry'] = difference
            differences_list.append(updated_row)
        elif difference.geom_type == 'MultiPolygon':
            for poly in difference.geoms:
                updated_row = original_row.copy()
                updated_row['geometry'] = poly
                differences_list.append(updated_row)

    def _create_result_dataframes(self, intersections, updated_gdf2_rows):
        """Create the result dataframes from intersection and difference lists."""
        if intersections:
            self.result_gdf = gpd.GeoDataFrame(intersections, crs=self.gdf2.crs)
            self.result_gdf['source_gdf1_id'] = self.gdf1.index[0]
            self.result_gdf['geometry_type'] = 'intersection'
        else:
            self.result_gdf = gpd.GeoDataFrame(columns=self.gdf2.columns.tolist() +
                                             ['source_gdf1_id', 'geometry_type'],
                                             crs=self.gdf2.crs)

        if updated_gdf2_rows:
            self.gdf2_excl = gpd.GeoDataFrame(updated_gdf2_rows, crs=self.gdf2.crs)
            self.gdf2_excl['geometry_type'] = 'original_remaining'
        else:
            self.gdf2_excl = gpd.GeoDataFrame(columns=self.gdf2.columns.tolist() +
                                            ['geometry_type'], crs=self.gdf2.crs)

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
        combined_gdf = gpd.GeoDataFrame(combined_gdf, geometry='geometry', crs=self.gdf2.crs)

        return combined_gdf

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

    def summary(self):
        """Print a summary of the intersection results."""
        if self.result_gdf is None or self.gdf2_excl is None:
            print("No results calculated. Call calculate_intersections() first.")
            return

        print("=== Polygon Intersection Summary ===")
        print(f"Original gdf1 polygons: {len(self.gdf1)}")
        print(f"Original gdf2 polygons: {len(self.gdf2)}")
        print(f"Intersection polygons: {len(self.result_gdf)}")
        print(f"Remaining gdf2 polygons: {len(self.gdf2_excl)}")
        print(f"Combined total polygons: {len(self.result_gdf) + len(self.gdf2_excl)}")

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

    # gdf2 with multiple polygons
    polygons2 = [
        Polygon([(1, 1), (4, 1), (4, 4), (1, 4)]),  # Will intersect
        Polygon([(2, 0), (5, 0), (5, 2), (2, 2)]),  # Will intersect
        Polygon([(0, 2), (2, 2), (2, 5), (0, 5)]),  # Will intersect
        Polygon([(4, 4), (6, 4), (6, 6), (4, 6)])   # Will NOT intersect
    ]
    gdf2 = gpd.GeoDataFrame({
        'id': [10, 20, 30, 40],
        'type': ['A', 'B', 'C', 'D'],
        'value': [100, 200, 300, 400]
    }, geometry=polygons2, crs='EPSG:4326')

    # Create intersector instance
    intersector = PolygonIntersector(gdf1, gdf2)

    # Calculate intersections using enhanced method
    intersector.calculate_intersections(method='enhanced')

    # Get results using different methods
    print("=== Using get_intersections() ===")
    result_gdf, gdf2_excl = intersector.get_intersections()
    print(f"Intersections: {len(result_gdf)} polygons")
    print(f"Remaining: {len(gdf2_excl)} polygons")

    print("\n=== Using get_combined_gdf() ===")
    combined_gdf = intersector.get_combined_gdf()
    print(f"Combined: {len(combined_gdf)} polygons")
    print("Geometry types:", combined_gdf['geometry_type'].value_counts().to_dict())

    print("\n=== Using get_all_results() ===")
    result_gdf, gdf2_excl, combined_gdf = intersector.get_all_results()
    print(f"All results - Intersections: {len(result_gdf)}, Remaining: {len(gdf2_excl)}, Combined: {len(combined_gdf)}")

    print("\n=== Summary ===")
    intersector.summary()

    # Test with different methods
    print("\n" + "="*50)
    print("Testing with basic method:")
    intersector_basic = PolygonIntersector(gdf1, gdf2)
    intersector_basic.calculate_intersections(method='basic')
    intersector_basic.summary()
