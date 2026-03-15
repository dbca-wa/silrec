from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import F, Max, Min, Q
#from django.contrib.postgres.fields import JSONField
from django.db.models.functions import Cast
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.gis.db.models import MultiPolygonField
from django.contrib.gis.db.models.fields import PolygonField
from django.contrib.gis.db.models.functions import Area

from django.db import connection

import re
import json
import geopandas as gpd
from rest_framework import serializers
import reversion
from reversion.models import Version

from dirtyfields import DirtyFieldsMixin

from silrec.components.main.models import (
    Document,
    ApplicationType,
    SecureFileField,
    RevisionedMixin,
)
#from silrec.components.forest_blocks.models import (
#    Polygon,
#)

import logging
logger = logging.getLogger(__name__)

User = get_user_model()

def update_proposal_doc_filename(instance, filename):
    return f"proposals/{instance.proposal.id}/documents/{filename}"

def update_proposal_comms_log_filename(instance, filename):
    return f"proposals/{instance.log_entry.proposal.id}/{filename}"


class AdditionalDocumentType(RevisionedMixin):
    name = models.CharField(max_length=255, null=True, blank=True)
    help_text = models.CharField(max_length=255, null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        db_table = 'additionaldocumenttype'
        app_label = "silrec"
        verbose_name = "Additional Document Type"
        ordering = ["name"]


class DefaultDocument(Document):
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    visible = models.BooleanField(
        default=True
    )  # to prevent deletion on file system, hidden and still be available in history

    class Meta:
        db_table = 'defaultdocument'
        app_label = "silrec"
        abstract = True

    def delete(self):
        if self.can_delete:
            return super().delete()
        logger.info(
            "Cannot delete existing document object after Application has been submitted "
            "(including document submitted before Application pushback to status Draft): {}".format(
                self.name
            )
        )

class ProposalDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="supporting_documents", on_delete=models.CASCADE
    )
    _file = SecureFileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        db_table = 'proposaldocument'
        app_label = "silrec"
        verbose_name = "Application Document"


class ShapefileDocumentQueryset(models.QuerySet):
    """Using a custom manager to make sure shapfiles are removed when a bulk .delete is called
    as having multiple files with the shapefile extensions in the same folder causes issues.
    """

    def delete(self):
        for obj in self:
            obj._file.delete()
        super().delete()


class ShapefileDocument(Document):
    objects = ShapefileDocumentQueryset.as_manager()

    proposal = models.ForeignKey(
        "Proposal", related_name="shapefile_documents", on_delete=models.CASCADE
    )
    _file = SecureFileField(upload_to=update_proposal_doc_filename, max_length=500)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    def delete(self):
        if self.can_delete:
            self._file.delete()
            return super().delete()
        logger.info(
            "Cannot delete existing document object after Proposal has been submitted "
            "(including document submitted before Proposal pushback to status Draft): {}".format(
                self.name
            )
        )

    class Meta:
        db_table = 'shapefiledocument'
        app_label = "silrec"


class ProposalAdditionalDocumentType(models.Model):
    proposal = models.ForeignKey(
        'Proposal', on_delete=models.CASCADE, related_name="additional_document_types"
    )
    additional_document_type = models.ForeignKey(
        AdditionalDocumentType, on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'proposaladditionaldocumenttype'
        app_label = "silrec"


class ProposalType(models.Model):
    PROPOSAL_TYPE_NEW = "new"
    PROPOSAL_TYPE_RENEWAL = "renewal"
    PROPOSAL_TYPE_AMENDMENT = "amendment"
    PROPOSAL_TYPE_MIGRATION = "migration"
    PROPOSAL_TYPES = [
        (PROPOSAL_TYPE_NEW, "New Proposal"),
        (PROPOSAL_TYPE_AMENDMENT, "Amendment"),
        (PROPOSAL_TYPE_RENEWAL, "Renewal"),
        (PROPOSAL_TYPE_MIGRATION, "Migration"),
    ]

    # class ProposalType(RevisionedMixin):
    code = models.CharField(max_length=30, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        # return 'id: {} code: {}'.format(self.id, self.code)
        return self.description

    class Meta:
        db_table = 'proposaltype'
        app_label = "silrec"


#class ProposalManager(models.Manager):
#    def get_queryset(self):
#        return (
#            super()
#            .get_queryset()
#            .select_related(
#                "proposal_type", "org_applicant", "application_type", "approval"
#            )
#        )

class ProposalManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .exclude(processing_status=Proposal.PROCESSING_STATUS_TEMP)
        )

class Proposal(RevisionedMixin, DirtyFieldsMixin):
    objects = ProposalManager()

    MODEL_PREFIX = "P"

    PROCESSING_STATUS_DRAFT = "draft"
    PROCESSING_STATUS_AMENDMENT_REQUIRED = "amendment_required"
    PROCESSING_STATUS_WITH_ASSESSOR = "with_assessor"
    PROCESSING_STATUS_WITH_ASSESSOR_TREATMENTS = "with_assessor_treatments"
    PROCESSING_STATUS_WITH_ASSESSOR_TASKS = "with_assessor_tasks"
    PROCESSING_STATUS_WITH_REVIEWER = "with_reviewer"
    PROCESSING_STATUS_REVIEW_COMPLETED = "review_Completed"
    PROCESSING_STATUS_DECLINED = "declined"
    PROCESSING_STATUS_DISCARDED = "discarded"
    PROCESSING_STATUS_TEMP = "temp"
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_DRAFT, "Draft"),
        (PROCESSING_STATUS_AMENDMENT_REQUIRED, "Amendment Required"),
        (PROCESSING_STATUS_WITH_ASSESSOR, "With Assessor"),
        (PROCESSING_STATUS_WITH_ASSESSOR_TREATMENTS, "With Assessor (Treatments)"),
        (PROCESSING_STATUS_WITH_ASSESSOR_TASKS, "With Assessor (Tasks)"),
        (PROCESSING_STATUS_WITH_REVIEWER, "With Reviewer"),
        (PROCESSING_STATUS_REVIEW_COMPLETED, "Review Completed"),
        (PROCESSING_STATUS_DECLINED, "Declined"),
        (PROCESSING_STATUS_DISCARDED, "Discarded"),
        (PROCESSING_STATUS_TEMP, "Temporary"),
    )

    COMPLIANCE_CHECK_STATUS_CHOICES = (
        ("not_checked", "Not Checked"),
        ("awaiting_returns", "Awaiting Returns"),
        ("completed", "Completed"),
        ("accepted", "Accepted"),
    )

    REVIEW_STATUS_CHOICES = (
        ("not_reviewed", "Not Reviewed"),
        ("awaiting_amendments", "Awaiting Amendments"),
        ("amended", "Amended"),
        ("accepted", "Accepted"),
    )

    proposal_type = models.ForeignKey(
        ProposalType, blank=True, null=True, on_delete=models.SET_NULL
    )
    proposed_issuance_approval = models.JSONField(blank=True, null=True)
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    lodgement_date = models.DateTimeField(blank=True, null=True)
    submitter = models.IntegerField(null=True)  # EmailUserRO
#    assigned_officer = models.IntegerField(null=True)  # EmailUserRO
#    assigned_approver = models.IntegerField(null=True)  # EmailUserRO
#    approved_by = models.IntegerField(null=True)  # EmailUserRO
    processing_status = models.CharField(
        "Processing Status",
        max_length=35,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_CHOICES[0][0],
    )
    prev_processing_status = models.CharField(max_length=30, blank=True, null=True)
#    review_status = models.CharField(
#        "Review Status",
#        max_length=30,
#        choices=REVIEW_STATUS_CHOICES,
#        default=REVIEW_STATUS_CHOICES[0][0],
#    )
    previous_application = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    #proposed_decline_status = models.BooleanField(default=False)
    # Special Fields
    title = models.CharField(max_length=255, null=True, blank=True)
    #title = models.CharField(max_length=255, db_index=True) for frequently searched fields
    application_type = models.ForeignKey(ApplicationType, on_delete=models.PROTECT)

    shapefile_json = models.JSONField('Source/Submitter (multi) polygon geometry', blank=True, null=True)
    geojson_data_hist = models.JSONField('History Polygons that intersect Source Polygons', blank=True, null=True)
    geojson_data_processed = models.JSONField('Source Polygon intersected with hist and split (multi) polygon geometry', blank=True, null=True)
    geojson_data_processed_iters = models.JSONField('Source Polygon intersected with hist and split (multi) polygon geometry', blank=True, null=True)
    migrated = models.BooleanField(default=False)

    class Meta:
        db_table = 'proposal'
        app_label = "silrec"
        verbose_name = "Proposal"

    def save(self, *args, **kwargs):
        # Clear out the cached
        #cache.delete(settings.CACHE_KEY_MAP_PROPOSALS)

        # Store the original values of fields we want to keep track of in
        # django reversion before they are overwritten by super() below
        original_processing_status = self._original_state['processing_status']
        #original_assessor_data = self._original_state['assessor_data']
        #original_comment_data = self._original_state['comment_data']

        super().save(*args, **kwargs)

        if self.lodgement_number == '':
            self.lodgement_number = 'P{0:06d}'.format(self.pk)
            self.save()

        # If the processing_status has changed then add a reversion comment
        # so we have a way of filtering based on the status changing
        if self.processing_status != original_processing_status:
            self.save(version_comment=f'processing_status: {self.processing_status}')

    @property
    def submitter_obj(self):
        return User.objects.get(id=self.submitter)

    @property
    def can_user_view(self):
        return True

#    @property
#    def shp_to_gdf(self):
#        return gpd.read_file(json.dumps(self.shapefile_json))

    @property
    def geojson_shpfile_to_gdf(self):
        """Return shapefile GeoJSON as a GeoDataFrame (read‑only)."""""
        return gpd.read_file(json.dumps(self.shapefile_json))

    @property
    def geojson_hist_to_gdf(self):
        """Return shapefile GeoJSON as a GeoDataFrame (read‑only)."""""
        return gpd.read_file(json.dumps(self.geojson_data_hist))

    @property
    def geojson_processed_to_gdf(self):
        """Return shapefile GeoJSON as a GeoDataFrame (read‑only)."""""
        return gpd.read_file(json.dumps(self.geojson_data_processed))

    def get_shapefile_attributes_status(self):
        """
        Returns a dictionary with:
        - 'gdf': GeoDataFrame of the shapefile
        - 'present_fields': list of attribute columns present in the shapefile
        - 'mandatory_fields': list of mandatory fields defined for this proposal's application_type
        - 'missing_mandatory': list of mandatory fields not present
        - 'optional_fields': list of optional fields defined
        - 'extra_fields': fields present but not defined in configuration
        - 'all_defined_fields': all configured fields for this application type
        """
        if not self.shapefile_json:
            return None

        gdf = self.geojson_shpfile_to_gdf
        present_fields = list(gdf.columns) if not gdf.empty else []

        # Get configuration for this proposal's application type
        configs = ShapefileAttributeConfig.objects.filter(
            application_type=self.application_type
        ).order_by('order')

        mandatory_fields = [c.field_name for c in configs if c.is_mandatory]
        optional_fields = [c.field_name for c in configs if not c.is_mandatory]
        all_defined = [c.field_name for c in configs]

        missing_mandatory = [f for f in mandatory_fields if f not in present_fields]
        extra_fields = [f for f in present_fields if f not in all_defined]

        return {
            'gdf': gdf,
            'present_fields': present_fields,
            'mandatory_fields': mandatory_fields,
            'missing_mandatory': missing_mandatory,
            'optional_fields': optional_fields,
            'extra_fields': extra_fields,
            'all_defined_fields': all_defined,
        }

    def check_planar_enforcement(self, geojson_data, area_tolerance=0.0001):
        """
        Check for overlapping polygons that exceed area_tolerance.

        Args:
            geojson_data: GeoJSON (string or dict) OR GeoPandas GeoDataFrame
            area_tolerance: Minimum intersection area in square meters to report (default: 0.0001 m²)

        Returns:
            List of dictionaries: [
                {
                    'polygon_1_id': str/int,
                    'polygon_2_id': str/int,
                    'intersection_area_m2': float,
                    'polygon_1_index': int,  # index in feature collection
                    'polygon_2_index': int   # index in feature collection
                },
                ...
            ]
            Returns empty list if no intersections found or invalid input.

            Eg.
                p=Proposal.objects.get(id=1)
                intersections = p.check_planar_enforcement(p.shapefile_json)
                intersections = p.check_planar_enforcement(gdf_shp_16)

                for idx, i in enumerate(intersections):
                    print(idx, i['intersection_area_m2'])
                0 0.0004
                1 0.0114
                2 0.1179

                intersections = p.check_planar_enforcement(list_state[0]['GDF_HIST'])
                for idx, i in enumerate(intersections):
                    print(idx, i['polygon_1_id'], i['polygon_2_id'], i['intersection_area_m2'], i['polygon_1_index'], i['polygon_2_index'])
                0 424207 424092 0.0007 16 65
                1 458410 458411 470.3053 20 31
                2 458425 458426 2.209 26 37

                plot_multi([list_state[0]['GDF_SHP'], list_state[0]['GDF_HIST'], list_state[0]['GDF_RESULT_COMBINED']])
                plot_overlay(list_state[0]['GDF_HIST'].iloc[[20]], list_state[0]['GDF_HIST'].iloc[[31]])
        """
        import geopandas as gpd
        from shapely.geometry import shape
        import json
        import pandas as pd
        import numpy as np

        if geojson_data is None:
            return []

        try:
            # Handle different input types
            gdf = None

            # Case 1: Already a GeoDataFrame
            if isinstance(geojson_data, gpd.GeoDataFrame):
                gdf = geojson_data.copy()

            # Case 2: GeoJSON string
            elif isinstance(geojson_data, str):
                try:
                    geojson_dict = json.loads(geojson_data)
                    gdf = gpd.read_file(json.dumps(geojson_dict))
                except:
                    # Try reading directly as file path or URL
                    try:
                        gdf = gpd.read_file(geojson_data)
                    except:
                        return []

            # Case 3: GeoJSON dict
            elif isinstance(geojson_data, dict):
                try:
                    gdf = gpd.read_file(json.dumps(geojson_data))
                except:
                    # Try reading as feature collection
                    features = geojson_data.get('features', [])
                    if features:
                        # Manual conversion
                        geoms = []
                        props_list = []
                        for feat in features:
                            geom = shape(feat.get('geometry', {}))
                            props = feat.get('properties', {})
                            geoms.append(geom)
                            props_list.append(props)

                        if geoms:
                            gdf = gpd.GeoDataFrame(props_list, geometry=geoms)

            # Case 4: List of features
            elif isinstance(geojson_data, list):
                geoms = []
                props_list = []
                for idx, item in enumerate(geojson_data):
                    if isinstance(item, dict):
                        if 'geometry' in item:
                            # Feature format
                            geom = shape(item.get('geometry', {}))
                            props = item.get('properties', {})
                        else:
                            # Assume it's a geometry dict
                            geom = shape(item)
                            props = {}

                        geoms.append(geom)
                        props_list.append(props)

                if geoms:
                    gdf = gpd.GeoDataFrame(props_list, geometry=geoms)

            else:
                return []

            # Validate we have a GeoDataFrame with data
            if gdf is None or gdf.empty:
                return []

            # Ensure we have a geometry column
            if 'geometry' not in gdf.columns:
                return []

            # Filter to only polygon/multipolygon geometries
            valid_types = ['Polygon', 'MultiPolygon']
            gdf = gdf[gdf.geometry.type.isin(valid_types)].copy()

            if len(gdf) < 2:
                return []

            # Reset index for clean tracking
            gdf = gdf.reset_index(drop=True)

            # Extract or create polygon IDs
            ids = []
            for idx, row in gdf.iterrows():
                # Look for ID in various possible columns
                polygon_id = None
                for id_field in ['polygon_id', 'id', 'fid', 'OBJECTID', 'OBJECTID_1', 'FID', 'index']:
                    if id_field in gdf.columns:
                        val = row[id_field]
                        if pd.notna(val) and val is not None:
                            polygon_id = str(val)
                            break

                # If no ID found, use index
                if polygon_id is None:
                    polygon_id = f"polygon_{idx}"

                ids.append({
                    'id': polygon_id,
                    'index': idx,
                    'properties': row.to_dict() if hasattr(row, 'to_dict') else {}
                })

            # Convert to projected CRS for accurate area calculation
            try:
                # Check if we have valid bounds
                if gdf.total_bounds is not None:
                    # Convert to numpy array if needed and check for any NaN values
                    bounds = np.array(gdf.total_bounds)
                    if not np.any(np.isnan(bounds)):
                        centroid_lon = (bounds[0] + bounds[2]) / 2
                        centroid_lat = (bounds[1] + bounds[3]) / 2

                        # Validate coordinates
                        if -180 <= centroid_lon <= 180 and -90 <= centroid_lat <= 90:
                            # UTM zones: 1-60, each 6 degrees wide
                            utm_zone = int((centroid_lon + 180) / 6) + 1
                            utm_zone = max(1, min(60, utm_zone))  # Clamp to valid range

                            # Choose hemisphere
                            if centroid_lat >= 0:
                                projected_crs = f"EPSG:326{utm_zone:02d}"  # Northern hemisphere
                            else:
                                projected_crs = f"EPSG:327{utm_zone:02d}"  # Southern hemisphere

                            try:
                                gdf_projected = gdf.to_crs(projected_crs)
                            except Exception as e:
                                logger.warning(f"UTM projection failed: {e}, trying Albers")
                                # Fallback to Albers Equal Area for Australia if available
                                try:
                                    gdf_projected = gdf.to_crs('EPSG:3577')  # GDA94 / Australian Albers
                                except:
                                    # Last resort: Web Mercator (approximate)
                                    gdf_projected = gdf.to_crs('EPSG:3857')
                        else:
                            # Invalid coordinates, use Web Mercator
                            gdf_projected = gdf.to_crs('EPSG:3857')
                    else:
                        # Bounds contain NaN, use Web Mercator
                        gdf_projected = gdf.to_crs('EPSG:3857')
                else:
                    # No bounds available, use Web Mercator
                    gdf_projected = gdf.to_crs('EPSG:3857')

            except Exception as e:
                logger.warning(f"CRS conversion failed, using original geometry for area calculation (areas may be inaccurate): {e}")
                gdf_projected = gdf

            # Check for intersections
            intersections = []
            n = len(gdf_projected)

            # Use spatial indexing for better performance if available
            try:
                from shapely.strtree import STRtree
                tree = STRtree(gdf_projected.geometry)

                for i in range(n):
                    geom_i = gdf_projected.geometry.iloc[i]

                    # Get potential intersecting geometries using spatial index
                    potential_matches = tree.query(geom_i)

                    for j in potential_matches:
                        if j <= i:  # Avoid duplicates and self-intersections
                            continue

                        geom_j = gdf_projected.geometry.iloc[j]

                        if geom_i.intersects(geom_j):
                            try:
                                intersection = geom_i.intersection(geom_j)

                                # Skip point/line intersections
                                if intersection.geom_type in ['Point', 'LineString', 'MultiPoint', 'MultiLineString']:
                                    continue

                                # Calculate area in square meters
                                # If we're in geographic coordinates, area will be in square degrees, which is wrong
                                # So we need to ensure we're in a projected CRS
                                if gdf_projected.crs and gdf_projected.crs.is_geographic:
                                    # Try one more time to project
                                    try:
                                        if gdf.total_bounds is not None:
                                            bounds = np.array(gdf.total_bounds)
                                            if not np.any(np.isnan(bounds)):
                                                centroid_lon = (bounds[0] + bounds[2]) / 2
                                                centroid_lat = (bounds[1] + bounds[3]) / 2
                                                if -180 <= centroid_lon <= 180 and -90 <= centroid_lat <= 90:
                                                    utm_zone = int((centroid_lon + 180) / 6) + 1
                                                    utm_zone = max(1, min(60, utm_zone))
                                                    if centroid_lat >= 0:
                                                        proj_crs = f"EPSG:326{utm_zone:02d}"
                                                    else:
                                                        proj_crs = f"EPSG:327{utm_zone:02d}"

                                                    # Create a small GeoDataFrame with just these two geometries
                                                    temp_gdf = gpd.GeoDataFrame(
                                                        geometry=[geom_i, geom_j],
                                                        crs=gdf_projected.crs
                                                    )
                                                    temp_gdf_proj = temp_gdf.to_crs(proj_crs)
                                                    intersection_proj = temp_gdf_proj.geometry.iloc[0].intersection(
                                                        temp_gdf_proj.geometry.iloc[1]
                                                    )
                                                    area_m2 = intersection_proj.area
                                                else:
                                                    area_m2 = intersection.area  # Will be inaccurate
                                            else:
                                                area_m2 = intersection.area  # Will be inaccurate
                                        else:
                                            area_m2 = intersection.area  # Will be inaccurate
                                    except:
                                        area_m2 = intersection.area  # Will be inaccurate
                                else:
                                    area_m2 = intersection.area

                                # Report if above tolerance
                                if area_m2 > area_tolerance:
                                    intersections.append({
                                        'polygon_1_id': ids[i]['id'],
                                        'polygon_2_id': ids[j]['id'],
                                        'intersection_area_m2': round(area_m2, 4),
                                        'polygon_1_index': ids[i]['index'],
                                        'polygon_2_index': ids[j]['index'],
                                        'polygon_1_properties': ids[i]['properties'],
                                        'polygon_2_properties': ids[j]['properties'],
                                        'intersection_geom_type': intersection.geom_type
                                    })
                            except Exception as e:
                                logger.warning(f"Error calculating intersection between {i} and {j}: {e}")
                                continue

            except ImportError:
                # Fallback to brute force if STRtree not available
                for i in range(n):
                    for j in range(i + 1, n):
                        geom_i = gdf_projected.geometry.iloc[i]
                        geom_j = gdf_projected.geometry.iloc[j]

                        if geom_i.intersects(geom_j):
                            try:
                                intersection = geom_i.intersection(geom_j)

                                if intersection.geom_type in ['Point', 'LineString', 'MultiPoint', 'MultiLineString']:
                                    continue

                                # Calculate area with CRS handling
                                if gdf_projected.crs and gdf_projected.crs.is_geographic:
                                    try:
                                        if gdf.total_bounds is not None:
                                            bounds = np.array(gdf.total_bounds)
                                            if not np.any(np.isnan(bounds)):
                                                centroid_lon = (bounds[0] + bounds[2]) / 2
                                                centroid_lat = (bounds[1] + bounds[3]) / 2
                                                if -180 <= centroid_lon <= 180 and -90 <= centroid_lat <= 90:
                                                    utm_zone = int((centroid_lon + 180) / 6) + 1
                                                    utm_zone = max(1, min(60, utm_zone))
                                                    if centroid_lat >= 0:
                                                        proj_crs = f"EPSG:326{utm_zone:02d}"
                                                    else:
                                                        proj_crs = f"EPSG:327{utm_zone:02d}"

                                                    temp_gdf = gpd.GeoDataFrame(
                                                        geometry=[geom_i, geom_j],
                                                        crs=gdf_projected.crs
                                                    )
                                                    temp_gdf_proj = temp_gdf.to_crs(proj_crs)
                                                    intersection_proj = temp_gdf_proj.geometry.iloc[0].intersection(
                                                        temp_gdf_proj.geometry.iloc[1]
                                                    )
                                                    area_m2 = intersection_proj.area
                                                else:
                                                    area_m2 = intersection.area
                                            else:
                                                area_m2 = intersection.area
                                        else:
                                            area_m2 = intersection.area
                                    except:
                                        area_m2 = intersection.area
                                else:
                                    area_m2 = intersection.area

                                if area_m2 > area_tolerance:
                                    intersections.append({
                                        'polygon_1_id': ids[i]['id'],
                                        'polygon_2_id': ids[j]['id'],
                                        'intersection_area_m2': round(area_m2, 4),
                                        'polygon_1_index': ids[i]['index'],
                                        'polygon_2_index': ids[j]['index'],
                                        'polygon_1_properties': ids[i]['properties'],
                                        'polygon_2_properties': ids[j]['properties'],
                                        'intersection_geom_type': intersection.geom_type
                                    })
                            except Exception as e:
                                logger.warning(f"Error calculating intersection between {i} and {j}: {e}")
                                continue

            return intersections

        except Exception as e:
            logger.error(f"Error in check_planar_enforcement: {e}")
            return []


    def check_all_geometries_planar(self, area_tolerance=0.0001):
        """
        Check all geometry fields for planar enforcement issues.

        Args:
            area_tolerance: Minimum intersection area in square meters

        Returns:
            Dictionary with results for each geometry type
        """
        results = {}

        # Check shapefile_json
        if self.shapefile_json:
            results['shapefile_json'] = self.check_planar_enforcement(
                self.shapefile_json,
                area_tolerance
            )

        # Check geojson_data_hist
        if self.geojson_data_hist:
            results['geojson_data_hist'] = self.check_planar_enforcement(
                self.geojson_data_hist,
                area_tolerance
            )

        # Check geojson_data_processed
        if self.geojson_data_processed:
            results['geojson_data_processed'] = self.check_planar_enforcement(
                self.geojson_data_processed,
                area_tolerance
            )

        # Check geojson_data_processed_iters if it exists
        if hasattr(self, 'geojson_data_processed_iters') and self.geojson_data_processed_iters:
            if isinstance(self.geojson_data_processed_iters, dict):
                # Handle iteration data
                iter_results = {}
                for key, iter_data in self.geojson_data_processed_iters.items():
                    if isinstance(iter_data, (dict, gpd.GeoDataFrame)):
                        iter_results[key] = self.check_planar_enforcement(
                            iter_data,
                            area_tolerance
                        )
                if iter_results:
                    results['geojson_data_processed_iters'] = iter_results

        return results

    def get_intersection_summary(self, geojson_data=None, area_tolerance=0.0001):
        """
        Get a simple summary of intersections without detailed properties.

        Args:
            geojson_data: Optional specific geometry to check (if None, checks all)
                        Can be GeoJSON (str/dict) or GeoDataFrame
            area_tolerance: Minimum intersection area in square meters

        Returns:
            List of simple intersection records
        """
        if geojson_data is not None:
            intersections = self.check_planar_enforcement(geojson_data, area_tolerance)
            return [
                {
                    'polygon_1_id': inter['polygon_1_id'],
                    'polygon_2_id': inter['polygon_2_id'],
                    'intersection_area_m2': inter['intersection_area_m2']
                }
                for inter in intersections
            ]
        else:
            # Check all and flatten
            all_results = self.check_all_geometries_planar(area_tolerance)
            simple_results = []

            for geom_type, intersections in all_results.items():
                if isinstance(intersections, list):
                    for inter in intersections:
                        simple_results.append({
                            'geometry_type': geom_type,
                            'polygon_1_id': inter['polygon_1_id'],
                            'polygon_2_id': inter['polygon_2_id'],
                            'intersection_area_m2': inter['intersection_area_m2']
                        })
                elif isinstance(intersections, dict):
                    # Handle nested iteration data
                    for iter_key, iter_intersections in intersections.items():
                        for inter in iter_intersections:
                            simple_results.append({
                                'geometry_type': f"{geom_type}[{iter_key}]",
                                'polygon_1_id': inter['polygon_1_id'],
                                'polygon_2_id': inter['polygon_2_id'],
                                'intersection_area_m2': inter['intersection_area_m2']
                            })

            return simple_results

    def geometries_are_planar(self, area_tolerance=0.0001):
        """
        Quick check if all geometries are planar (no intersections above tolerance).

        Returns:
            bool: True if no intersections found, False otherwise
        """
        all_results = self.check_all_geometries_planar(area_tolerance)

        for geom_type, intersections in all_results.items():
            if isinstance(intersections, list) and intersections:
                return False
            elif isinstance(intersections, dict):
                for iter_intersections in intersections.values():
                    if iter_intersections:
                        return False

        return True


class SQLReport(models.Model):
    """Model for storing SQL query reports with dynamic WHERE clauses"""

    # Report Type options
    REPORT_TYPES = [
        ('polygon', 'Polygon Analysis'),
        ('cohort', 'Chort Analysis'),
        ('treatment', 'Treatment Analysis'),
        ('operation', 'Operation Analysis'),
        ('custom', 'Custom Report'),
    ]

    # Export Format options
    EXPORT_FORMATS = [
        ('excel', 'Excel (.xlsx)'),
        ('csv', 'CSV (.csv)'),
        ('pdf', 'PDF (.pdf)'),
        ('shapefile', 'Shapefile (.shp)'),
    ]

    # Field Type choices
    FIELD_TYPE_CHOICES = [
        ('select', 'Single Select (Dropdown)'),
        ('multiselect', 'Multi-Select (Select2)'),
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('date', 'Date Picker'),
        ('year', 'Year Select'),
        ('month', 'Month Select'),
        ('range', 'Range (Two Values)'),
    ]

    # Operator choices for WHERE clauses
    OPERATOR_CHOICES = [
        ('=', 'Equals'),
        ('!=', 'Not Equals'),
        ('>', 'Greater Than'),
        ('<', 'Less Than'),
        ('>=', 'Greater Than or Equal'),
        ('<=', 'Less Than or Equal'),
        ('LIKE', 'Contains'),
        ('NOT LIKE', 'Does Not Contain'),
        ('IN', 'In List'),
        ('NOT IN', 'Not In List'),
        ('IS NULL', 'Is Null'),
        ('IS NOT NULL', 'Is Not Null'),
        ('BETWEEN', 'Between'),
        ('YEAR', 'Year Equals'),
        ('MONTH', 'Month Equals'),
        ('DATE', 'Date Equals'),
    ]

    name = models.CharField(max_length=255, unique=True, help_text="Report name for dropdown selection")
    description = models.TextField(blank=True, help_text="Description of what this report shows")

    # Main SQL Query
    base_sql = models.TextField(
        help_text="Main SQL query without WHERE clause. Use {where_clause} placeholder. Example: SELECT * FROM table {where_clause}"
    )

    # Dynamic WHERE clauses configuration
    where_clauses = models.JSONField(
        default=list,
        blank=True,
        help_text="""
        JSON array of WHERE clause definitions. Example:
        [
            {
                "field": "year",
                "operator": "YEAR",
                "parameter_name": "year",
                "label": "Select Year",
                "field_type": "select",
                "options_query": "SELECT DISTINCT EXTRACT(YEAR FROM date_column) FROM table ORDER BY 1 DESC",
                "default_value": "2024",
                "required": true
            },
            {
                "field": "supply",
                "operator": "=",
                "parameter_name": "supply",
                "label": "Select Supply",
                "field_type": "multiselect",
                "options_query": "SELECT DISTINCT supply FROM compartments ORDER BY supply",
                "required": true
            }
        ]
        """
    )

    # ORDER BY clause
    order_by = models.TextField(
        blank=True,
        help_text="ORDER BY clause. Example: region ASC, district DESC"
    )

    # Report metadata
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='custom')
    export_formats = models.JSONField(
        default=list,
        help_text="JSON list of allowed export formats: ['excel', 'csv', 'pdf', 'shapefile']"
    )

    # Display options
    columns = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of column definitions for display. If empty, all columns will be shown."
    )

    # Permissions
    allowed_groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        help_text="User groups that can run this report"
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports'
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sqlreport'
        app_label = 'silrec'
        ordering = ['name']
        verbose_name = 'SQL Report'
        verbose_name_plural = 'SQL Reports'

    def __str__(self):
        return f"{self.name} ({self.report_type})"

    def clean(self):
        """Validate the SQL and JSON configurations"""
        super().clean()

        # Validate base SQL contains placeholder
        if '{where_clause}' not in self.base_sql:
            raise ValidationError(
                "Base SQL must contain '{where_clause}' placeholder for WHERE clause insertion"
            )

        # Validate WHERE clauses JSON
        if self.where_clauses:
            try:
                for clause in self.where_clauses:
                    if not all(k in clause for k in ['field', 'operator', 'parameter_name', 'label', 'field_type']):
                        raise ValidationError(
                            "Each WHERE clause must have 'field', 'operator', 'parameter_name', 'label', and 'field_type'"
                        )

                    # Validate field_type
                    valid_field_types = [choice[0] for choice in self.FIELD_TYPE_CHOICES]
                    if clause['field_type'] not in valid_field_types:
                        raise ValidationError(
                            f"Invalid field_type '{clause['field_type']}'. Must be one of {valid_field_types}"
                        )

                    # Validate operator
                    valid_operators = [op[0] for op in self.OPERATOR_CHOICES]
                    if clause['operator'] not in valid_operators:
                        raise ValidationError(
                            f"Invalid operator '{clause['operator']}'. Must be one of {valid_operators}"
                        )

                    # For multiselect, operator should typically be IN
                    if clause['field_type'] == 'multiselect' and clause.get('operator') not in ['IN', 'NOT IN']:
                        clause['operator'] = 'IN'  # Auto-correct
                        clause['recommended_operator'] = 'IN'

                    # For range field_type, operator should be BETWEEN
                    if clause['field_type'] == 'range' and clause.get('operator') != 'BETWEEN':
                        clause['operator'] = 'BETWEEN'  # Auto-correct

            except (TypeError, KeyError) as e:
                raise ValidationError(f"Invalid WHERE clauses configuration: {str(e)}")

        # Validate export formats
        if self.export_formats:
            valid_formats = [fmt[0] for fmt in self.EXPORT_FORMATS]
            for fmt in self.export_formats:
                if fmt not in valid_formats:
                    raise ValidationError(
                        f"Invalid export format '{fmt}'. Must be one of {valid_formats}"
                    )

    def get_full_sql(self, parameters=None):
        """Generate full SQL with WHERE clause based on parameters"""
        where_clauses = []
        query_params = []

        if parameters and self.where_clauses:
            for clause in self.where_clauses:
                param_name = clause['parameter_name']
                field_type = clause.get('field_type', 'select')

                if param_name in parameters and parameters[param_name]:
                    field = clause['field']
                    operator = clause['operator']
                    value = parameters[param_name]

                    # Handle different field types
                    if field_type == 'multiselect':
                        # For multiselect, we should use IN operator with multiple values
                        if isinstance(value, list):
                            if value:  # Only add clause if list is not empty
                                # Filter out empty values
                                filtered_values = [v for v in value if v and str(v).strip()]
                                if filtered_values:
                                    placeholders = ','.join(['%s'] * len(filtered_values))
                                    where_clauses.append(f"{field} IN ({placeholders})")
                                    query_params.extend(filtered_values)
                        elif value and str(value).strip():  # Single value
                            where_clauses.append(f"{field} = %s")
                            query_params.append(value)

                    elif field_type == 'range':
                        # Handle range (BETWEEN operator)
                        if isinstance(value, list) and len(value) == 2:
                            where_clauses.append(f"{field} BETWEEN %s AND %s")
                            query_params.extend(value)

                    elif operator == 'YEAR':
                        where_clauses.append(f"EXTRACT(YEAR FROM {field}) = %s")
                        query_params.append(value)

                    elif operator == 'MONTH':
                        where_clauses.append(f"EXTRACT(MONTH FROM {field}) = %s")
                        query_params.append(value)

                    elif operator == 'DATE':
                        where_clauses.append(f"DATE({field}) = %s")
                        query_params.append(value)

                    elif operator == 'IN':
                        # Handle both single values and arrays for IN
                        if isinstance(value, list):
                            # Filter out empty values
                            filtered_values = [v for v in value if v and str(v).strip()]
                            if filtered_values:
                                placeholders = ','.join(['%s'] * len(filtered_values))
                                where_clauses.append(f"{field} IN ({placeholders})")
                                query_params.extend(filtered_values)
                        elif value and str(value).strip():
                            where_clauses.append(f"{field} = %s")
                            query_params.append(value)

                    elif operator == 'LIKE':
                        where_clauses.append(f"{field} ILIKE %s")
                        query_params.append(f"%{value}%")

                    elif operator == 'NOT LIKE':
                        where_clauses.append(f"{field} NOT ILIKE %s")
                        query_params.append(f"%{value}%")

                    elif operator == 'BETWEEN':
                        if isinstance(value, list) and len(value) == 2:
                            where_clauses.append(f"{field} BETWEEN %s AND %s")
                            query_params.extend(value)

                    elif operator in ['IS NULL', 'IS NOT NULL']:
                        where_clauses.append(f"{field} {operator}")

                    else:
                        where_clauses.append(f"{field} {operator} %s")
                        query_params.append(value)

        # Build WHERE clause
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        else:
            where_clause = ""

        # Add ORDER BY if specified
        order_by_clause = f"ORDER BY {self.order_by}" if self.order_by else ""

        # Build full SQL
        full_sql = self.base_sql.format(where_clause=where_clause)
        if order_by_clause:
            full_sql += " " + order_by_clause

        return full_sql, query_params

    def get_parameter_options(self, parameter_name):
        """Get dynamic options for a parameter from its options_query"""
        for clause in self.where_clauses:
            if clause['parameter_name'] == parameter_name and 'options_query' in clause:
                from django.db import connection
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(clause['options_query'])
                        return [str(row[0]) for row in cursor.fetchall()]
                except Exception:
                    return []
        return []

    @property
    def formatted_sql(self):
        """Return formatted SQL for display"""
        return self.base_sql.format(where_clause="WHERE ...") + (f" ORDER BY {self.order_by}" if self.order_by else "")

    def get_available_fields(self):
        """Extract field names from the SQL query"""
        fields = []

        try:
            # Remove comments from SQL
            sql = re.sub(r'--.*$', '', self.base_sql, flags=re.MULTILINE)
            sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

            # Extract SELECT clause (everything between SELECT and FROM)
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
            if not select_match:
                return []

            select_clause = select_match.group(1)

            # Split by commas, handling nested parentheses
            in_parentheses = 0
            current_field = ""
            for char in select_clause:
                if char == '(':
                    in_parentheses += 1
                elif char == ')':
                    in_parentheses -= 1

                if char == ',' and in_parentheses == 0:
                    # End of field
                    field = self._extract_field_name(current_field.strip())
                    if field:
                        fields.append(field)
                    current_field = ""
                else:
                    current_field += char

            # Add the last field
            if current_field:
                field = self._extract_field_name(current_field.strip())
                if field:
                    fields.append(field)

            # Also try to extract table aliases for better display
            from_match = re.search(r'FROM\s+(.*?)(?:\s+WHERE|\s+GROUP BY|\s+ORDER BY|$)',
                                  sql, re.IGNORECASE | re.DOTALL)
            if from_match:
                from_clause = from_match.group(1)
                # Extract table aliases (e.g., "table t" or "table AS t")
                table_aliases = re.findall(r'(\w+)(?:\s+AS)?\s+(\w+)\b', from_clause, re.IGNORECASE)
                table_dict = {alias: table for table, alias in table_aliases}

                # Update fields with table aliases if available
                for i, field in enumerate(fields):
                    if '.' in field:
                        table_part, column_part = field.split('.', 1)
                        if table_part in table_dict:
                            fields[i] = f"{table_part}.{column_part}"

        except Exception as e:
            print(f"Error extracting fields from SQL: {e}")
            import traceback
            traceback.print_exc()

        # Remove duplicates and sort
        return sorted(list(set(f for f in fields if f)))

    def _extract_field_name(self, field_expression):
        """Extract field name from a SQL expression"""
        # Remove "DISTINCT" keyword
        field_expression = re.sub(r'^DISTINCT\s+', '', field_expression, flags=re.IGNORECASE)

        # Handle COUNT(DISTINCT ...) differently
        if re.match(r'COUNT\s*\(.*DISTINCT.*\)', field_expression, re.IGNORECASE):
            # Just return the entire expression for complex aggregates
            return field_expression

        # Remove aggregate functions (keep the column inside)
        field_expression = re.sub(r'^\w+\(([^)]+)\)', r'\1', field_expression, flags=re.IGNORECASE)

        # Remove "AS alias" or just alias after whitespace
        field_expression = re.split(r'\s+(?:AS\s+)?\w+$', field_expression, flags=re.IGNORECASE)[0]

        # Remove extra whitespace
        field_expression = field_expression.strip()

        # If it's a simple column name or table.column, return it
        if re.match(r'^(\w+\.)?\w+$', field_expression):
            return field_expression

        return None

    def get_table_fields(self):
        """Get fields from actual database tables in the query"""
        fields = []
        try:
            # Extract table names from FROM and JOIN clauses
            sql = self.base_sql.upper()

            # Get all table references (simplified)
            table_patterns = [
                r'FROM\s+(\w+(?:\.\w+)?)\s+(\w+)',
                r'JOIN\s+(\w+(?:\.\w+)?)\s+(\w+)\s+ON',
                r'FROM\s+(\w+(?:\.\w+)?)',
                r'JOIN\s+(\w+(?:\.\w+)?)'
            ]

            tables = []
            for pattern in table_patterns:
                matches = re.findall(pattern, sql, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if isinstance(match, tuple):
                        tables.extend([m for m in match if m])
                    else:
                        tables.append(match)

            # Remove duplicates
            tables = list(set(tables))

            # Get columns from each table
            for table in tables:
                try:
                    # Try to get actual columns from database
                    with connection.cursor() as cursor:
                        cursor.execute(f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = %s
                            ORDER BY ordinal_position
                        """, [table.split('.')[-1]])  # Remove schema if present
                        columns = [row[0] for row in cursor.fetchall()]

                    for column in columns:
                        fields.append(f"{table}.{column}")

                except Exception as e:
                    print(f"Could not get columns for table {table}: {e}")
                    # Fallback: just add the table reference
                    fields.append(f"{table}.*")

        except Exception as e:
            print(f"Error extracting table fields: {e}")

        return fields



class TextSearchModelConfig(models.Model):
    """Model configuration for text search"""
    from django.utils.translation import gettext_lazy as _

    MODEL_KEY_CHOICES = [
        ('proposal', 'Proposals'),
        ('polygon', 'Polygons'),
        ('cohort', 'Cohorts'),
        ('treatment', 'Treatments'),
        ('treatment_xtra', 'Treatment Extras'),
        ('survey_assessment_document', 'Survey Documents'),
        ('silviculturist_comment', 'Silviculturist Comments'),
        ('prescription', 'Prescriptions'),
    ]

    key = models.CharField(
        max_length=50,
        choices=MODEL_KEY_CHOICES,
        unique=True,
        verbose_name=_("Model Key")
    )

    model_name = models.CharField(
        max_length=200,
        verbose_name=_("Django Model Path"),
        help_text=_("Format: 'app_label.ModelName' (e.g., 'silrec.Proposal')")
    )

    display_name = models.CharField(
        max_length=100,
        verbose_name=_("Display Name")
    )

    # Comma-separated list of searchable fields
    search_fields = models.TextField(
        verbose_name=_("Search Fields"),
        help_text=_("Comma-separated list of field names to search in this model")
    )

    date_field = models.CharField(
        max_length=100,
        default="created_on",
        verbose_name=_("Date Field"),
        help_text=_("Field name for creation date")
    )

    id_field = models.CharField(
        max_length=100,
        default="id",
        verbose_name=_("ID Field"),
        help_text=_("Field name for the record ID")
    )

    # JSON field for detail fields
    detail_fields = models.JSONField(
        default=list,
        verbose_name=_("Detail Fields"),
        help_text=_("List of field names to show in details column")
    )

    url_pattern = models.CharField(
        max_length=500,
        verbose_name=_("URL Pattern"),
        help_text=_("URL pattern for detail view. Use {id} as placeholder for record ID")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Display Order")
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_search_configs"
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'textsearchmodelconfig'
        app_label='silrec'
        verbose_name = _("Text Search Model Configuration")
        verbose_name_plural = _("Text Search Model Configurations")
        ordering = ['order', 'display_name']

    def __str__(self):
        return f"{self.display_name} ({self.key})"

    def get_search_fields_list(self):
        """Return search fields as list"""
        if not self.search_fields:
            return []
        return [field.strip() for field in self.search_fields.split(',')]


class TextSearchFieldDisplay(models.Model):
    """Field display name configuration"""
    from django.utils.translation import gettext_lazy as _

    field_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Field Name")
    )

    display_name = models.CharField(
        max_length=100,
        verbose_name=_("Display Name")
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Display Order")
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_field_displays"
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'textsearchfielddisplay'
        app_label='silrec'
        verbose_name = _("Text Search Field Display")
        verbose_name_plural = _("Text Search Field Displays")
        ordering = ['order', 'field_name']

    def __str__(self):
        return f"{self.field_name} → {self.display_name}"


class ShapefileAttributeConfig(models.Model):
    """
    Defines expected attributes for shapefiles uploaded to a proposal
    based on the application type.
    """
    DATA_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('date', 'Date'),
    ]

    application_type = models.ForeignKey(
            ApplicationType,
            on_delete=models.CASCADE,
            related_name='shapefile_attributes',
            verbose_name=_("Application Type")
    )
    field_name = models.CharField(
            max_length=255,
            verbose_name=_("Field Name"),
            help_text=_("Exact name of the attribute column in the shapefile")
    )
    display_name = models.CharField(
            max_length=255,
            blank=True,
            verbose_name=_("Display Name"),
            help_text=_("Human‑readable label (optional)")
    )
    is_mandatory = models.BooleanField(
            default=False,
            verbose_name=_("Mandatory"),
            help_text=_("If checked, the shapefile must contain this attribute")
    )
    is_reserved = models.BooleanField(
            default=False,
            verbose_name=_("Is Reserved"),
            help_text=_("If checked, the shapefile's polygon will NOT be merged")
    )
    data_type = models.CharField(
            max_length=50,
            choices=DATA_TYPE_CHOICES,
            default='string',
            verbose_name=_("Data Type"),
            help_text=_("Expected data type (for future validation)")
    )
    target_db_field = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Target Database Field"),
        help_text=_("Optional mapping to a database field, e.g., 'silrec.forest_blocks.polygon.sp_code'")
    )
    order = models.PositiveIntegerField(
            default=0,
            verbose_name=_("Order"),
            help_text=_("Display order in admin/list views")
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shapefileattributeconfig'
        app_label = 'silrec'
        verbose_name = _("Shapefile Attribute Configuration")
        verbose_name_plural = _("Shapefile Attribute Configurations")
        ordering = ['application_type', 'order', 'field_name']
        unique_together = [['application_type', 'field_name']]

    def __str__(self):
        return f"{self.application_type} – {self.field_name} (mandatory={self.is_mandatory})"

    def clean(self):
        if self.is_mandatory and not self.field_name:
            raise ValidationError({"field_name": _("Field name cannot be empty for mandatory attributes.")})

    def get_target_db_field_parts(self):
        """
        Parse the target_db_field string into (app_label, model_name, field_name).
        Returns a tuple of three strings, any of which may be None if parsing fails.
        """
        if not self.target_db_field:
            return None, None, None
        parts = self.target_db_field.split('.')
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            # assume model_name.field_name, app_label omitted
            return None, parts[0], parts[1]
        else:
            return None, None, None


class RequestMetrics(models.Model):
    """ groups related audit logs."""
    proposal = models.ForeignKey(
        Proposal,
        related_name="request_metrics",
        on_delete=models.DO_NOTHING
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        # related_name='request_metrics'  # optional
    )
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'requestmetrics'
        app_label = 'silrec'
        ordering = ['-timestamp']
        verbose_name = 'Processing Log'
        verbose_name_plural = 'Processing Logs'

    def __str__(self):
        return f"{self.proposal} – {self.user} at {self.timestamp}"

    def get_record_ids_for_table(self, table_name, operation='ALL'):
        """
        Return a list of distinct record IDs from audit logs for a given table.
        :param table_name: The database table name (e.g., 'polygon', 'cohort')
        :param operation: 'ALL', 'INSERT', 'UPDATE', or 'DELETE'
        """
        qs = self.audit_logs.filter(table_name=table_name)
        if operation != 'ALL':
            qs = qs.filter(operation=operation)
        return list(qs.values_list('record_id', flat=True).distinct())

    def get_polygon_ids(self, operation='ALL'):
        """Return polygon record IDs from audit logs, optionally filtered by operation."""
        return self.get_record_ids_for_table('polygon', operation)

    def polygons_to_gdf(self, operation='ALL'):
       from silrec.utils.helper import polygons_to_gdf
       return polygons_to_gdf(self.get_polygon_ids(operation))

    def get_cohort_ids(self, operation='ALL'):
        """Return cohort record IDs from audit logs, optionally filtered by operation."""
        return self.get_record_ids_for_table('cohort', operation)

    def get_assign_cht_to_ply_ids(self, operation='ALL'):
        """Return assign_cht_to_ply record IDs from audit logs, optionally filtered by operation."""
        return self.get_record_ids_for_table('assign_cht_to_ply', operation)

    def check_planar_enforcement(self, operation='ALL', area_tolerance=0.0001):
        """
        Check if any polygons affected in this request (by operation) overlap
        with an intersection area greater than area_tolerance (in square meters).

        Parameters:
            operation (str): 'ALL', 'INSERT', 'UPDATE', or 'DELETE'.
            area_tolerance (float): minimum intersection area (m²) to consider as problematic.
                                    Use 0.0 to detect any overlap (even tiny slivers).

        Returns:
            dict: {
                'has_intersections': bool,
                'intersections': list of tuples (polygon_id_1, polygon_id_2, intersection_area),
                'gdf': GeoDataFrame of the polygons (with polygon_id as index) or None if no polygons.
            }
        """
        from silrec.utils.helper import polygons_to_gdf

        poly_ids = self.get_polygon_ids(operation)
        if len(poly_ids) < 2:
            return {'has_intersections': False, 'intersections': [], 'gdf': None}

        gdf = polygons_to_gdf(poly_ids)
        # Ensure polygon_id is the index for easy lookup
        gdf = gdf.set_index('polygon_id')

        intersections = []
        ids = list(gdf.index)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                geom_i = gdf.loc[ids[i], 'geometry']
                geom_j = gdf.loc[ids[j], 'geometry']
                if geom_i.intersects(geom_j):
                    intersection = geom_i.intersection(geom_j)
                    area = intersection.area
                    if area > area_tolerance:
                        intersections.append((ids[i], ids[j], area))

        return {
            'has_intersections': len(intersections) > 0,
            'intersections': intersections,
            'gdf': gdf
        }

# ---------- Updated AuditLog model ----------
class AuditLog(models.Model):
    OPERATION_CHOICES = (
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    )

    table_name = models.CharField(max_length=255, db_index=True)
    record_id = models.PositiveIntegerField(db_index=True)   # now integer only
    request_metrics = models.ForeignKey(
        RequestMetrics,
        related_name="audit_logs",
        on_delete=models.CASCADE
    )
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    iter_seq = models.PositiveIntegerField('Iteration')
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auditlog'
        app_label = 'silrec'
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
        ]
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.operation} on {self.table_name}#{self.record_id} at {self.start_time}"


## -------------------------------------------------------------------------------------
#
## Helper to collect all relation names (forward + reverse) for reversion.follow
#def get_follow_fields(model):
#    from django.db.models import ForeignKey, OneToOneField, ManyToManyField
#    from django.db.models.fields.related import ManyToOneRel, OneToOneRel, ManyToManyRel
#
#    follow = []
#    for field in model._meta.get_fields():
#        if field.is_relation:
#            # Forward relations: use the field name
#            if isinstance(field, (ForeignKey, OneToOneField, ManyToManyField)):
#                follow.append(field.name)
#            # Reverse relations: use the reverse accessor name (e.g. 'treatment_set')
#            # NOTE: Reverse relations can increase the size of revision data --> can cause performance issues
#            elif isinstance(field, (ManyToOneRel, OneToOneRel, ManyToManyRel)):
#                follow.append(field.get_accessor_name())
#    return follow
#
#
## Register models with django-reversion
from reversion import register

#register(AdditionalDocumentType, follow=get_follow_fields(AdditionalDocumentType))
register(AdditionalDocumentType, follow=['proposaladditionaldocumenttype_set'])
register(ProposalDocument, follow=['proposal'])
register(ShapefileDocument, follow=['proposal'])
register(ProposalAdditionalDocumentType, follow=['proposal', 'additional_document_type'])
register(ProposalType, follow=[])
#register(Proposal, follow=['proposal_type', 'previous_application', 'application_type'])
register(Proposal, follow=[
    'proposal_type',
    'previous_application',
    'application_type',
    'polygons',              # Reverse relation to Polygon
    'shapefile_documents',   # Shapefile documents
    'supporting_documents',  # Other documents
    #'request_metrics'        # Request metrics
])
#register(ProposalGeometry, follow=['proposal', 'copied_from'])
#register(AmendmentReason, follow=[])
#register(ProposalRequest, follow=[])
#register(AmendmentRequest, follow=[])
register(SQLReport, follow=['created_by', 'allowed_groups'])
register(TextSearchModelConfig, follow=['created_by'])
register(TextSearchFieldDisplay, follow=['created_by'])
register(ShapefileAttributeConfig, follow=['application_type'])

