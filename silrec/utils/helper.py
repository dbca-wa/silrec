import geopandas as gpd
from shapely import wkb
from silrec.components.forest_blocks.models import Polygon

def polygons_to_gdf(polygon_ids):
    """
    Fetch polygons with the given IDs from the database and return a GeoDataFrame.

    Returns: GDF (CRS set to EPSG:28350)
    -------

    Usage:
        ssm = ShapefileSliversMerger(gdf_shp_16, proposal_id=1, threshold=5)
        list_state = ssm.create_gdf()

        poly_ids = list_state[0]['GDF_RESULT_COMBINED'].poly_id_new.to_list()
        gdf = polygons_to_gdf(poly_ids)

        plot_gdf(gdf)
        plot_multi([gdf, list_state[0]['GDF_RESULT_COMBINED']])
    """
    qs = Polygon.objects.filter(polygon_id__in=polygon_ids)
    data = list(qs.values())

    if not data:
        return gpd.GeoDataFrame(columns=[f.name for f in Polygon._meta.fields], crs="EPSG:28350")

    df = gpd.GeoDataFrame(data)

    # Convert GEOSGeometry objects (in 'geom' column) to WKB bytes, then to Shapely geometries
    df['geometry'] = gpd.GeoSeries.from_wkb(
        df['geom'].apply(lambda g: bytes(g.wkb) if g else None),  # memoryview -> bytes
        crs=28350
    )

    df = df.drop(columns=['geom']).set_geometry('geometry')
    return df
