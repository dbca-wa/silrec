from django.contrib.auth import get_user_model
import logging
import json
from datetime import datetime, date
from decimal import Decimal
from django.db import transaction, models
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from silrec.components.forest_blocks.models import Polygon#, PolygonAudit
from silrec.components.proposals.models import AuditLog
from silrec.utils.create_audit_log import AuditLogger
from copy import deepcopy

logger = logging.getLogger(__name__)

User = get_user_model()

def write_gdf_to_polygon(gdf_result, user_id=None):
    """
    Write GeoDataFrame to polygon table using Django ORM.
    Handles repeated polygon_ids, prioritizes poly_type (CUT > BASE > others),
    and adds 'poly_id_new' column to the returned GeoDataFrame.

    Returns:
        tuple: (operations_summary, gdf_result_with_new_ids)
    """
    with transaction.atomic():
        # Create a copy to add the new IDs
        gdf_result_with_ids = gdf_result.copy()
        gdf_result_with_ids['poly_id_new'] = None

        # Capture current state for audit trail
        #current_records = _get_current_polygon_records()

        # Track operations
        ops_summary = {
            'new_records': 0,
            'updated_records': 0,
            'skipped_records': 0,
            'new_polygon_ids': [],
            'updated_polygon_ids': [],
            'priority_updates': []
        }

        # Sort by poly_type priority (CUT > BASE > others)
        gdf_sorted = _sort_gdf_by_polytype_priority(gdf_result_with_ids)

        # Build a map of polygon_id -> highest priority poly_type in the input
        poly_type_map = _create_poly_type_map(gdf_sorted)

        for idx, row in gdf_sorted.iterrows():
            polygon_id = row['polygon_id']
            poly_type = row.get('poly_type', 'OTHER')

            # Check if polygon_id already exists in the database
            existing_polygon = Polygon.objects.filter(polygon_id=polygon_id).first()

            if existing_polygon is None:
                # New polygon_id → insert
                _insert_new_polygon(row, user_id)
                ops_summary['new_records'] += 1
                ops_summary['new_polygon_ids'].append(polygon_id)
                gdf_result_with_ids.loc[idx, 'poly_id_new'] = polygon_id
                logger.info(f"Inserted new record with polygon_id: {polygon_id}, poly_type: {poly_type}")

            else:
                # Polygon_id already exists
                if _is_duplicate_in_gdf(gdf_sorted, polygon_id, idx):
                    # This polygon_id appears multiple times in the input
                    if _should_update_based_on_priority(poly_type_map, polygon_id, poly_type):
                        # Higher priority → update the existing record
                        _update_existing_polygon(row, polygon_id, user_id)
                        ops_summary['updated_records'] += 1
                        ops_summary['updated_polygon_ids'].append(polygon_id)
                        ops_summary['priority_updates'].append(polygon_id)
                        gdf_result_with_ids.loc[idx, 'poly_id_new'] = polygon_id
                        logger.info(f"Priority update - Updated existing record with polygon_id: {polygon_id}, new poly_type: {poly_type}")
                    else:
                        # Lower priority → create a new record with a new polygon_id
                        new_polygon_id = _get_next_polygon_id()
                        _insert_duplicate_polygon(row, new_polygon_id, user_id)
                        ops_summary['new_records'] += 1
                        ops_summary['new_polygon_ids'].append(new_polygon_id)
                        gdf_result_with_ids.loc[idx, 'poly_id_new'] = new_polygon_id
                        logger.info(f"Created duplicate record: {polygon_id} -> {new_polygon_id}, poly_type: {poly_type}")
                else:
                    # First occurrence of this polygon_id in the input → update
                    _update_existing_polygon(row, polygon_id, user_id)
                    ops_summary['updated_records'] += 1
                    ops_summary['updated_polygon_ids'].append(polygon_id)
                    gdf_result_with_ids.loc[idx, 'poly_id_new'] = polygon_id
                    logger.info(f"Updated existing record with polygon_id: {polygon_id}, poly_type: {poly_type}")

        # Capture final state and create audit records
        #final_records = _get_current_polygon_records()
        #_create_audit_records(current_records, final_records, user_id)

        logger.info(f"Operation completed: {ops_summary}")
        return ops_summary, gdf_result_with_ids


# ------------------------------------------------------------------------------
# Priority sorting helpers (pandas logic, unchanged)
# ------------------------------------------------------------------------------

def _sort_gdf_by_polytype_priority(gdf):
    """Sort GeoDataFrame by poly_type priority: CUT > BASE > others."""
    if 'poly_type' not in gdf.columns:
        return gdf

    priority_order = {'CUT': 1, 'BASE': 2}
    gdf_sorted = gdf.copy()
    gdf_sorted['_priority'] = gdf_sorted['poly_type'].map(priority_order).fillna(3)
    gdf_sorted = gdf_sorted.sort_values(['_priority', 'polygon_id'])
    gdf_sorted = gdf_sorted.drop('_priority', axis=1)
    return gdf_sorted

def _create_poly_type_map(gdf):
    """Map each polygon_id to its highest priority poly_type in the input."""
    if 'poly_type' not in gdf.columns:
        return {}

    poly_type_map = {}
    priority_order = {'CUT': 1, 'BASE': 2}

    for _, row in gdf.iterrows():
        pid = row['polygon_id']
        ptype = row['poly_type']
        current_prio = priority_order.get(ptype, 3)

        if pid not in poly_type_map:
            poly_type_map[pid] = ptype
        else:
            existing_prio = priority_order.get(poly_type_map[pid], 3)
            if current_prio < existing_prio:
                poly_type_map[pid] = ptype

    return poly_type_map

def _should_update_based_on_priority(poly_type_map, polygon_id, new_poly_type):
    """Return True if new_poly_type has higher priority than what's already processed."""
    if polygon_id not in poly_type_map:
        return True

    priority_order = {'CUT': 1, 'BASE': 2}
    existing_priority = priority_order.get(poly_type_map[polygon_id], 3)
    new_priority = priority_order.get(new_poly_type, 3)
    return new_priority < existing_priority

def _is_duplicate_in_gdf(gdf, polygon_id, current_index):
    """Check if this polygon_id appears multiple times in the GeoDataFrame."""
    total_count = (gdf['polygon_id'] == polygon_id).sum()
    first_idx = gdf[gdf['polygon_id'] == polygon_id].index[0]
    return current_index != first_idx

# ------------------------------------------------------------------------------
# Django ORM database helpers
# ------------------------------------------------------------------------------

def _get_current_polygon_records():
    """
    Fetch all polygon records from the database.
    Returns a dict {polygon_id: {field: value}} for audit comparison.
    """
    records = {}
    for poly in Polygon.objects.all().values():
        # Convert datetime/date/Decimal to JSON‑serializable types later
        records[poly['polygon_id']] = poly
    return records

def _insert_new_polygon(row, user_id):
    """Insert a new polygon record. proposal_id is set only if poly_type == 'BASE'."""
    geom = GEOSGeometry(row['geometry'].wkt) if hasattr(row['geometry'], 'wkt') else None
    proposal_id = row.get('proposal_id') if row.get('poly_type') == 'BASE' else None

    ply = Polygon.objects.create(
        polygon_id=row['polygon_id'],
        name=row['name'],
        compartment_id=row['compartment'],
        area_ha=row['area_ha'],
        sp_code=row['sp_code'],
        proposal_id=proposal_id,
        geom=geom,
        created_by=user_id,
        updated_by=user_id,
        # created_on/updated_on are auto‑set if the model uses auto_now_add/auto_now
    )

    al = AuditLogger(Polygon, ply, 'INSERT', user_id, proposal_id, None, ply)

def _insert_duplicate_polygon(row, new_polygon_id, user_id):
    """Insert a duplicate polygon with a new polygon_id."""
    geom = GEOSGeometry(row['geometry'].wkt) if hasattr(row['geometry'], 'wkt') else None
    proposal_id = row.get('proposal_id') if row.get('poly_type') == 'BASE' else None

    ply = Polygon.objects.create(
        polygon_id=new_polygon_id,
        name=row['name'],
        compartment_id=row['compartment'],
        area_ha=row['area_ha'],
        sp_code=row['sp_code'],
        proposal_id=proposal_id,
        geom=geom,
        created_by=user_id,
        updated_by=user_id,
    )

    al = AuditLogger(Polygon, ply, 'INSERT', user_id, proposal_id, None, ply)

def _update_existing_polygon(row, polygon_id, user_id):
    """
    Update an existing polygon record.
    proposal_id is set only if the current DB value is NULL.
    """
    poly = Polygon.objects.select_for_update().get(polygon_id=polygon_id)
    poly_orig = deepcopy(poly)

    # Update basic fields
    poly.name = row['name']
    poly.compartment_id = row['compartment']
    poly.area_ha = row['area_ha']
    poly.sp_code = row['sp_code']
    if hasattr(row['geometry'], 'wkt'):
        poly.geom = GEOSGeometry(row['geometry'].wkt)
    poly.updated_by = user_id

    # proposal_id: set only if currently NULL and poly_type == 'BASE'
    if poly.proposal_id is None and row.get('poly_type') == 'BASE':
        poly.proposal_id = row.get('proposal_id')

    poly.save()

    al = AuditLogger(Polygon, poly, 'UPDATE', user_id, poly.proposal_id, poly_orig, poly)

def _get_next_polygon_id():
    """Return the next available polygon_id (max existing + 1)."""
    max_id = Polygon.objects.aggregate(models.Max('polygon_id'))['polygon_id__max']
    return (max_id or 0) + 1

# Inside write_polygons_to_db.py (updated)


#def _create_audit_records(before_state, after_state, user_id):
#    """
#    Create audit entries for inserted/updated polygons.
#    before_state and after_state are dicts: {polygon_id: {field: value}}
#    user_id can be a User instance or a string (username).
#    """
#    # Resolve user object if user_id is a string
#    if isinstance(user_id, str):
#        try:
#            user = User.objects.get(username=user_id)
#        except User.DoesNotExist:
#            user = None
#    else:
#        user = user_d
#
#    table_name = Polygon._meta.db_table
#    all_ids = set(before_state.keys()) | set(after_state.keys())
#
#    for pid in all_ids:
#        before = before_state.get(pid)
#        after = after_state.get(pid)
#
#        before_json = _prepare_for_json(before) if before else None
#        after_json = _prepare_for_json(after) if after else None
#
#        if before is None and after is not None:
#            # Insert
#            AuditLog.objects.create(
#                table_name=table_name,
#                record_id=pid,
#                operation='INSERT',
#                new_values=after_json,
#                user=user,
#            )
#        elif before is not None and after is not None and before != after:
#            # Update
#            AuditLog.objects.create(
#                table_name=table_name,
#                record_id=pid,
#                operation='UPDATE',
#                old_values=before_json,
#                new_values=after_json,
#                user=user,
#            )

def _prepare_for_json(obj):
    """Convert datetime/date/Decimal to JSON‑serializable types."""
    if isinstance(obj, dict):
        return {k: _prepare_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

