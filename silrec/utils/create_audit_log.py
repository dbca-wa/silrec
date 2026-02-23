from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.gis.geos import GEOSGeometry
import geopandas as gpd
from shapely.geometry import shape
import json

from silrec.components.proposals.models import AuditLog


class AuditLogger:
    """
        AuditLogger to track INSERT/UPDATE/DELETE's

        from silrec.utils.create_audit_log import AuditLogger
        a=AuditLogger(Polygon, ply, 'INSERT', None, 1, ply, ply)
        a.create()
    """

    class AuditLogEncoder(DjangoJSONEncoder):
        '''
        Custom encoder to handle GEOS geometries
        '''
        def default(self, o):
            if isinstance(o, GEOSGeometry):
                # Convert geometry to GeoJSON dict
                return json.loads(o.geojson)
            return super().default(o)

    def __init__(self, model, obj, operation, user_id, proposal_id,
                 old_vals=None, new_vals=None, fields=None):

        self.model = model
        self.obj = obj
        self.operation = operation
        self.user_id = user_id
        self.proposal_id = proposal_id
        self.old_vals = old_vals
        self.new_vals = new_vals
        self.fields = fields

    def _to_dict(self, value):
        """Convert a model instance or dict to a dictionary. Return None if value is None."""
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        # Assume it's a model instance
        return model_to_dict(value, fields=self.fields)

    def _make_json_serializable(self, data):
        """Recursively convert data to JSON‑serializable types using the custom encoder."""
        if data is None:
            return None
        # Round-trip through JSON with our encoder to handle geometries, dates, etc.
        return json.loads(json.dumps(data, cls=self.AuditLogEncoder))

    def create(self):
        valid_ops = ['INSERT', 'UPDATE', 'DELETE']
        if self.operation not in valid_ops:
            raise ValueError(f"Operation must be one of {valid_ops}")

        # Convert old_vals and new_vals to dictionaries
        old_dict = self._to_dict(self.old_vals)
        new_dict = self._to_dict(self.new_vals)

        # If no explicit values were given, fall back to the current object's state
        if old_dict is None and self.operation != 'INSERT':
            old_dict = model_to_dict(self.obj, fields=self.fields)
        if new_dict is None and self.operation != 'DELETE':
            new_dict = model_to_dict(self.obj, fields=self.fields)

        # Ensure both dictionaries are JSON‑serializable
        old_dict = self._make_json_serializable(old_dict)
        new_dict = self._make_json_serializable(new_dict)

        # Create the audit log entry
        al = AuditLog.objects.create(
            table_name=self.model._meta.db_table,
            record_id=self.obj.pk,          # The object's primary key
            operation=self.operation,
            user_id=self.user_id,
            proposal_id=self.proposal_id,
            old_values=old_dict,
            new_values=new_dict
        )
        return al


    def geojson_to_geometry(self, geojson):
        """
        geom_dict = {
            'type': 'Polygon',
            'coordinates': [[
                [398040.3991463588, 6220270.892941184],
                [398039.66526621644, 6220265.923952607],
                [398041.1742557226, 6220276.1418727795],
                [398040.3991463588, 6220270.892941184]
            ]]
        }
        polygon = geojson_to_geometry(geom_dict)
        """
        if isinstance(geojson, dict):
            geojson = json.dumps(geojson)
        return GEOSGeometry(geojson)


    def geojson_to_gdf(self, geojson, crs=None):
        """
        Convert GeoJSON data (dict or string) to a GeoPandas GeoDataFrame.

        from silrec.utils.create_audit_log import AuditLogger
        a=AuditLogger(Polygon, ply, 'INSERT', None, 1, ply, ply, fields=['geom'])

        geom_dict = {
            'type': 'Polygon',
            'coordinates': [[
                [398040.3991463588, 6220270.892941184],
                [398039.66526621644, 6220265.923952607],
                [398041.1742557226, 6220276.1418727795],
                [398040.3991463588, 6220270.892941184]
            ]]
        }

        a.geojson_to_gdf(geom_dict)
        plot_gdf(a.geojson_to_gdf(geom_dict))

        """
        # If input is string, parse it to dict
        if isinstance(geojson, str):
            geojson = json.loads(geojson)

        # If input is a single geometry (type: Point, Polygon, etc.)
        if geojson.get('type') and 'coordinates' in geojson:
            # Convert to Shapely geometry using shape()
            geom = shape(geojson)
            gdf = gpd.GeoDataFrame(geometry=[geom], crs=crs)

        # If input is a single feature (type: Feature)
        elif geojson.get('type') == 'Feature':
            # Extract geometry and properties
            geom = shape(geojson['geometry'])
            props = geojson.get('properties', {})
            gdf = gpd.GeoDataFrame([props], geometry=[geom], crs=crs)

        # If input is a feature collection (type: FeatureCollection)
        elif geojson.get('type') == 'FeatureCollection':
            features = geojson.get('features', [])
            # Build list of geometries and properties
            geoms = []
            props = []
            for feat in features:
                geoms.append(shape(feat['geometry']))
                props.append(feat.get('properties', {}))
            gdf = gpd.GeoDataFrame(props, geometry=geoms, crs=crs)

        else:
            raise ValueError("Unsupported GeoJSON structure. Must be a geometry, feature, or feature collection.")

        return gdf

