import json
import logging
import os
import re
import sys
from zipfile import ZipFile

from shapely import wkt
import geopandas as gpd
import pytz
import requests
import subprocess
from django.apps import apps
from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.gis.geos.collections import MultiPolygon
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
#from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from silrec.settings import OGR2OGR, CRS_GDA94

from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger

#from leaseslicensing.components.tenure.models import (
#    LGA,
#    Act,
#    Category,
#    District,
#    Identifier,
#    Name,
#    Region,
#    SiteName,
#    Tenure,
#    Vesting,
#)

logger = logging.getLogger(__name__)

def save_geometry(
    request,
    instance,
    component,
    geometry_data,
    foreign_key_field=None,
    source_type='proponent',
):
    instance_name = instance._meta.model.__name__
    logger.info(f"\n\n\nSaving {instance_name} geometry")

    if not geometry_data:
        logger.warning(f"No {instance_name} geometry to save")
        return

    if not foreign_key_field:
        # this is the name of the foreign key field on the <Instance Type>Geometry model
        # Had to add this as no way to know for sure the name of the foreign key field based on introspection
        # i.e. competitive_process contains an underscore but the django model name does not
        foreign_key_field = instance_name.lower()

    geometry = json.loads(geometry_data)
    InstanceGeometry = apps.get_model("leaseslicensing", f"{instance_name}Geometry")
    if (
        0 == len(geometry["features"])
        and 0
        == InstanceGeometry.objects.filter(**{foreign_key_field: instance}).count()
    ):
        # No feature to save and no feature to delete
        logger.warning(f"{instance_name} geometry has no features to save or delete")
        return

    action = request.data.get("action", None)

    geometry_ids = []
    for feature in geometry.get("features"):
        # check if feature is a polygon, continue if not
        if feature.get("geometry").get("type") != "Polygon":
            logger.warning(
                f"{instance_name}: {instance} contains a feature that is not a polygon: {feature}"
            )
            continue

        # Create a Polygon object from the open layers feature
        polygon = Polygon(feature.get("geometry").get("coordinates")[0])

        specs = tenure_layer_specification()
        test_polygon = (
            invert_xy_coordinates([polygon])[0] if specs["invert_xy"] else polygon
        )

        if not polygon_intersects_with_layer(
            test_polygon,
            specs["server_url"],
            specs["layer_name"],
            specs["properties"],
            specs["version"],
            specs["the_geom"],
        ):
            # if it doesn't, raise a validation error (this should be prevented in the front end
            # and is here just in case
            raise ValidationError(
                "One or more polygons do not intersect with the DBCA Lands and Waters layer"
            )

        # If it does intersect, save it and set intersects to true
        geometry_data = {
            f"{foreign_key_field}_id": instance.id,
            "polygon": polygon,
            "intersects": True,  # probably redunant now that we are not allowing non-intersecting geometries
        }
        InstanceGeometrySaveSerializer = getattr(
            sys.modules[f"leaseslicensing.components.{component}.serializers"],
            f"{instance_name}GeometrySaveSerializer",
        )
        geometry_data["source_type"] = source_type
        if feature.get("id"):
            logger.info(
                f"Updating existing {instance_name} geometry: {feature.get('id')} for Proposal: {instance}"
            )
            try:
                geometry = InstanceGeometry.objects.get(id=feature.get("id"))
            except InstanceGeometry.DoesNotExist:
                logger.warning(
                    f"{instance_name} geometry does not exist: {feature.get('id')}"
                )
                continue
            geometry_data["drawn_by"] = geometry.drawn_by
            source_user = EmailUser.objects.get(id=geometry.drawn_by)
            geometry_data["source_name"] = (
                geometry.source_name
                if geometry.source_name
                else source_user.get_full_name()
            )
            geometry_data["locked"] = (
                action in ["submit"]
                and geometry.drawn_by == request.user.id
                or geometry.locked
            )
            serializer = InstanceGeometrySaveSerializer(geometry, data=geometry_data)
        else:
            logger.info(f"Creating new geometry for {instance_name}: {instance}")
            geometry_data["drawn_by"] = request.user.id
            geometry_data["source_name"] = request.user.get_full_name()
            geometry_data["locked"] = action in ["submit"]
            serializer = InstanceGeometrySaveSerializer(data=geometry_data)

        serializer.is_valid(raise_exception=True)
        proposalgeometry_instance = serializer.save()
        logger.info(f"Saved {instance_name} geometry: {proposalgeometry_instance}")
        geometry_ids.append(proposalgeometry_instance.id)

    # Remove any proposal geometries from the db that are no longer in the proposal_geometry that was submitted
    # Prevent deletion of polygons that are locked after status change (e.g. after submit)
    # or have been drawn by another user
    deleted_geometries = (
        InstanceGeometry.objects.filter(**{foreign_key_field: instance})
        .exclude(Q(id__in=geometry_ids) | Q(locked=True) | ~Q(drawn_by=request.user.id))
        .delete()
    )
    if deleted_geometries[0] > 0:
        logger.info(
            f"Deleted {instance_name} geometries: {deleted_geometries} for {instance}"
        )

def get_secure_file_url(instance, file_field_name, revision_id=None):
    base_path = settings.SECURE_FILE_API_BASE_PATH
    if revision_id:
        return f"{base_path}{instance._meta.model.__name__}/{instance.id}/{file_field_name}/{revision_id}/"
    return (
        f"{base_path}{instance._meta.model.__name__}/{instance.id}/{file_field_name}/"
    )


def get_secure_document_url(instance, related_name="documents", document_id=None):
    base_path = settings.SECURE_DOCUMENT_API_BASE_PATH
    if document_id:
        return f"{base_path}{instance._meta.model.__name__}/{instance.id}/{related_name}/{document_id}/"
    return f"{base_path}{instance._meta.model.__name__}/{instance.id}/{related_name}/"


def polygons_to_gdf():
    from silrec.components.forest_blocks.models import Polygon

    # TODO place in cache
    geo_series_list = []
    crs_list = []
    for poly in Polygon.objects.all():
        shapely_multi_polygon = wkt.loads(poly.geom.wkt)
        geo_series_list.append(shapely_multi_polygon)
        crs_list.append(poly.geom.srs.srid)

    # confirm all polygons geometries have same CRS
    if len(set(crs_list)) > 1:
        raise Exception(f'Geometry CRS is not unique {list(set(crs_list))}')
    gdf = gpd.GeoDataFrame(geometry=geo_series_list, crs=CRS_GDA94) # EPSG:28350
    return gdf

def get_processed_json_obj(gdf_single):
    ssm = ShapefileSliversMerger(gdf_single)
    gdf_result = ssm.create_gdf()
    return ssm.processed_to_json_obj()


def validate_map_files(request, instance, foreign_key_field=None):
    # Validates shapefiles uploaded with via the proposal map or the competitive process map.
    # Shapefiles are valid when the shp, shx, and dbf extensions are provided
    # and when they intersect with DBCA legislated land or water polygons

    valid_geometry_saved = False

    logger.debug(f"Shapefile documents: {instance.shapefile_documents.all()}")

    if not instance.shapefile_documents.exists():
        raise ValidationError(
            "Please attach at least a .shp, .shx, and .dbf file (the .prj file is optional but recommended)"
        )

    # Shapefile extensions shp (geometry), shx (index between shp and dbf), dbf (data) are essential
    shp_file_qs = instance.shapefile_documents.filter(
        Q(name__endswith=".shp")
        | Q(name__endswith=".shx")
        | Q(name__endswith=".dbf")
        | Q(name__endswith=".prj")
    )

    # Validate shapefile and all the other related files are present
    if not shp_file_qs:
        raise ValidationError(
            "You can only attach files with the following extensions: .shp, .shx, and .dbf"
        )

    shp_files = shp_file_qs.filter(name__endswith=".shp").count()
    shx_files = shp_file_qs.filter(name__endswith=".shx").count()
    dbf_files = shp_file_qs.filter(name__endswith=".dbf").count()

    if shp_files != 1 or shx_files != 1 or dbf_files != 1:
        raise ValidationError(
            "Please attach at least a .shp, .shx, and .dbf file (the .prj file is optional but recommended)"
        )

    # Add the shapefiles to a zip file for archiving purposes
    # (as they are deleted after being converted to proposal geometry)
    shapefile_archive_name = (
        os.path.splitext(instance.shapefile_documents.first().path)[0]
        + "-"
        + timezone.now().strftime("%Y%m%d%H%M%S")
        + ".zip"
    )
    shapefile_archive = ZipFile(shapefile_archive_name, "w")
    for shp_file_obj in shp_file_qs:
        shapefile_archive.write(shp_file_obj.path, shp_file_obj.name)
    shapefile_archive.close()

    # A list of all uploaded shapefiles
    shp_file_objs = shp_file_qs.filter(Q(name__endswith=".shp"))

    gdf_full = polygons_to_gdf()

    if len(shp_file_objs) > 1:
        raise ValidationError("Can only upload one shapefile combination at a time")

    #import ipdb; ipdb.set_trace()
    gdf = gpd.read_file(shp_file_objs[0].path)  # Shapefile to GeoDataFrame

    if gdf.empty:
        raise ValidationError(f"Geometry is empty in {shp_file_objs[0].name}")

    import ipdb; ipdb.set_trace()
    if not gdf.crs or gdf.crs.srs.lower() != CRS_GDA94.lower():
        gdf.set_crs(CRS_GDA94, inplace=True) # epsg:28350
    elif not gdf.crs or gdf.crs.srs.lower() != CRS_GDA94.lower():
        gdf.to_crs(CRS_GDA94, inplace=True) # epsg:28350

    result = gdf.overlay(gdf_full, how='intersection')
    if result.empty:
        raise ValidationError(
            "The input shapefile does not intersect with any historical polygons currently in the system"
        )
    else:
        valid_geometry_saved = True

    # Only accept polygons
    geometries = gdf.geometry  # GeoSeries
    geom_type = geometries.geom_type.values[0]
    if geom_type not in ("Polygon", "MultiPolygon"):
        raise ValidationError(f"Geometry of type {geom_type} not allowed")

    result_ogr = subprocess.run(f'{OGR2OGR} -t_srs EPSG:4326 -f GeoJSON /vsistdout/ {shp_file_objs[0].path}', capture_output=True, text=True, check=True, shell=True)
    shp_json = json.loads(result_ogr.stdout)

    instance.shapefile_json = shp_json
    import ipdb; ipdb.set_trace()
    instance.shp_processed_json = get_processed_json_obj(gpd.read_file(json.dumps(shp_json)))
    instance.save()

    # Delete all shapefile documents so the user can upload another one if they wish.
    instance.shapefile_documents.all().delete()

    return valid_geometry_saved


def populate_gis_data(instance, geometries_attribute, foreign_key_field=None):
    """Fetches required GIS data from the server defined in settings.GIS_SERVER_URL
    and saves it to the instance (Proposal or Competitive Process)"""
    import ipdb;ipdb.set_trace()
    instance_name = instance._meta.model.__name__

    logger.info(
        "Populating GIS data for %s: %s", instance_name, instance.lodgement_number
    )

    if not foreign_key_field:
        foreign_key_field = instance_name.lower()

#    populate_gis_data_lands_and_waters(
#        instance, geometries_attribute, foreign_key_field
#    )  # Covers Identifiers, Names, Acts, Tenures and Categories
#    populate_gis_data_regions(instance, geometries_attribute, foreign_key_field)
#    populate_gis_data_districts(instance, geometries_attribute, foreign_key_field)
#    populate_gis_data_lgas(instance, geometries_attribute, foreign_key_field)
    logger.info(
        "-> Finished populating GIS data for %s: %s",
        instance_name,
        instance.lodgement_number,
    )

