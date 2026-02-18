from sqlalchemy import create_engine, text, MetaData, Table, select, and_
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
import json
import logging

def write_gdf_to_tmp_polygon(gdf_result, engine, current_user="system"):
    """
    Write GeoDataFrame to tmp_polygon table with handling for repeated polygon_ids
    and create audit trail. Prioritizes poly_type in order: CUT > BASE > others.
    Also adds 'poly_id_new' column to gdf_result with the final polygon IDs.

    Args:
        gdf_result: GeoDataFrame with polygon data (must contain 'poly_type' column)
        engine: SQLAlchemy engine
        current_user: User performing the operation

    Returns:
        tuple: (operations_summary, gdf_result_with_new_ids)
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a copy of gdf_result to add the new IDs
    gdf_result_with_ids = gdf_result.copy()
    gdf_result_with_ids['poly_id_new'] = None  # Initialize the new column

    try:
        # Create audit table if it doesn't exist
        create_audit_table(session)

        # Get current state of tmp_polygon before changes
        current_records = get_current_tmp_polygon_records(session)

        # Track operations
        operations_summary = {
            'new_records': 0,
            'updated_records': 0,
            'skipped_records': 0,
            'new_polygon_ids': [],
            'updated_polygon_ids': [],
            'priority_updates': []  # Track which updates were due to priority
        }

        # Sort gdf_result by poly_type priority for processing order
        gdf_sorted = sort_gdf_by_polytype_priority(gdf_result_with_ids)

        # Store poly_type information for priority decisions
        poly_type_map = create_poly_type_map(gdf_sorted)

        # Process each row in the sorted GeoDataFrame
        for idx, row in gdf_sorted.iterrows():
            polygon_id = row['polygon_id']
            poly_type = row.get('poly_type', 'OTHER')  # Default to 'OTHER' if not specified

            # Check if this polygon_id already exists in tmp_polygon
            existing_count = count_existing_polygon_id(session, polygon_id)

            if existing_count == 0:
                # New polygon_id - insert as is (without poly_type since it's not in table)
                insert_new_polygon(session, row, current_user)
                operations_summary['new_records'] += 1
                operations_summary['new_polygon_ids'].append(polygon_id)
                # Set poly_id_new to the original polygon_id
                gdf_result_with_ids.loc[idx, 'poly_id_new'] = polygon_id
                logger.info(f"Inserted new record with polygon_id: {polygon_id}, poly_type: {poly_type}")

            else:
                # Polygon_id exists - check if we need to create a new record or update based on priority
                if is_duplicate_in_gdf(gdf_sorted, polygon_id, idx):
                    # This is a duplicate in the current gdf_result - check priority
                    if should_update_based_on_priority(poly_type_map, polygon_id, poly_type):
                        # Higher priority poly_type - update existing record
                        update_existing_polygon(session, row, polygon_id, current_user)
                        operations_summary['updated_records'] += 1
                        operations_summary['updated_polygon_ids'].append(polygon_id)
                        operations_summary['priority_updates'].append(polygon_id)
                        # Set poly_id_new to the original polygon_id (updated existing record)
                        gdf_result_with_ids.loc[idx, 'poly_id_new'] = polygon_id
                        logger.info(f"Priority update - Updated existing record with polygon_id: {polygon_id}, new poly_type: {poly_type}")
                    else:
                        # Lower priority poly_type - create new record with new polygon_id
                        new_polygon_id = get_next_polygon_id(session)
                        insert_duplicate_polygon(session, row, new_polygon_id, current_user)
                        operations_summary['new_records'] += 1
                        operations_summary['new_polygon_ids'].append(new_polygon_id)
                        # Set poly_id_new to the new polygon_id
                        gdf_result_with_ids.loc[idx, 'poly_id_new'] = new_polygon_id
                        logger.info(f"Created duplicate record: {polygon_id} -> {new_polygon_id}, poly_type: {poly_type}")
                else:
                    # First occurrence of this polygon_id in gdf - update existing record
                    update_existing_polygon(session, row, polygon_id, current_user)
                    operations_summary['updated_records'] += 1
                    operations_summary['updated_polygon_ids'].append(polygon_id)
                    # Set poly_id_new to the original polygon_id (updated existing record)
                    gdf_result_with_ids.loc[idx, 'poly_id_new'] = polygon_id
                    logger.info(f"Updated existing record with polygon_id: {polygon_id}, poly_type: {poly_type}")

        # Get final state and create audit records
        final_records = get_current_tmp_polygon_records(session)
        create_audit_records(session, current_records, final_records, current_user)

        session.commit()

        logger.info(f"Operation completed: {operations_summary}")
        # Return both the operations summary and the updated gdf with new IDs
        return operations_summary, gdf_result_with_ids

    except Exception as e:
        session.rollback()
        logger.error(f"Error writing to tmp_polygon: {e}")
        raise
    finally:
        session.close()

def sort_gdf_by_polytype_priority(gdf):
    """Sort GeoDataFrame by poly_type priority: CUT > BASE > others"""
    if 'poly_type' not in gdf.columns:
        # If no poly_type column, return as is
        return gdf

    # Define priority order - CHANGED: CUT now has highest priority (1), BASE has medium (2)
    priority_order = {'CUT': 1, 'BASE': 2}  # CHANGED: Swapped CUT and BASE

    # Add priority column
    gdf_sorted = gdf.copy()
    gdf_sorted['_priority'] = gdf_sorted['poly_type'].map(priority_order).fillna(3)

    # Sort by priority and then by polygon_id for consistency
    gdf_sorted = gdf_sorted.sort_values(['_priority', 'polygon_id'])
    gdf_sorted = gdf_sorted.drop('_priority', axis=1)

    return gdf_sorted

def create_poly_type_map(gdf):
    """Create a mapping of polygon_id to its highest priority poly_type"""
    if 'poly_type' not in gdf.columns:
        return {}

    poly_type_map = {}
    priority_order = {'CUT': 1, 'BASE': 2}  # CHANGED: Swapped CUT and BASE

    for _, row in gdf.iterrows():
        polygon_id = row['polygon_id']
        poly_type = row['poly_type']
        current_priority = priority_order.get(poly_type, 3)

        # Only keep the highest priority poly_type for each polygon_id
        if polygon_id not in poly_type_map:
            poly_type_map[polygon_id] = poly_type
        else:
            existing_priority = priority_order.get(poly_type_map[polygon_id], 3)
            if current_priority < existing_priority:
                poly_type_map[polygon_id] = poly_type

    return poly_type_map

def should_update_based_on_priority(poly_type_map, polygon_id, new_poly_type):
    """
    Check if the new poly_type has higher priority than what we've already processed
    Returns True if new poly_type should replace existing one
    """
    if polygon_id not in poly_type_map:
        return True

    # Define priority order (lower number = higher priority) - CHANGED: CUT now has highest priority
    priority_order = {'CUT': 1, 'BASE': 2}  # CHANGED: Swapped CUT and BASE
    #priority_order = {'BASE': 1, 'CUT': 2}  # CHANGED: Swapped CUT and BASE

    existing_poly_type = poly_type_map[polygon_id]
    existing_priority = priority_order.get(existing_poly_type, 3)
    new_priority = priority_order.get(new_poly_type, 3)

    # Update if new poly_type has higher priority (lower number)
    return new_priority < existing_priority

# Modified helper functions (remove poly_type from database queries)
def get_current_tmp_polygon_records(session):
    """Get current state of tmp_polygon table"""
    result = session.execute(text("""
        SELECT polygon_id, name, compartment, area_ha, sp_code, created_on, created_by
        FROM tmp_polygon
    """))
    return {row[0]: dict(row._mapping) for row in result}

def ___insert_new_polygon(session, row, current_user):
    """Insert a new polygon record"""
    session.execute(text("""
        INSERT INTO tmp_polygon (
            polygon_id, name, compartment, area_ha, sp_code, geom,
            created_on, created_by, updated_on, updated_by
        ) VALUES (
            :polygon_id, :name, :compartment, :area_ha, :sp_code, ST_GeomFromEWKT(:geom),
            CURRENT_TIMESTAMP, :created_by, CURRENT_TIMESTAMP, :updated_by
        )
    """), {
        'polygon_id': row['polygon_id'],
        'name': row['name'],
        'compartment': row['compartment'],
        'area_ha': row['area_ha'],
        'sp_code': row['sp_code'],
        'geom': row['geometry'].wkt if hasattr(row['geometry'], 'wkt') else None,
        'created_by': current_user,
        'updated_by': current_user
    })

def ___insert_duplicate_polygon(session, row, new_polygon_id, current_user):
    """Insert a duplicate polygon with a new polygon_id"""
    session.execute(text("""
        INSERT INTO tmp_polygon (
            polygon_id, name, compartment, area_ha, sp_code, geom,
            created_on, created_by, updated_on, updated_by
        ) VALUES (
            :polygon_id, :name, :compartment, :area_ha, :sp_code, ST_GeomFromEWKT(:geom),
            CURRENT_TIMESTAMP, :created_by, CURRENT_TIMESTAMP, :updated_by
        )
    """), {
        'polygon_id': new_polygon_id,
        'name': row['name'],
        'compartment': row['compartment'],
        'area_ha': row['area_ha'],
        'sp_code': row['sp_code'],
        'geom': row['geometry'].wkt if hasattr(row['geometry'], 'wkt') else None,
        'created_by': current_user,
        'updated_by': current_user
    })

def ___update_existing_polygon(session, row, polygon_id, current_user):
    """Update an existing polygon record"""
    session.execute(text("""
        UPDATE tmp_polygon
        SET name = :name, compartment = :compartment, area_ha = :area_ha,
            sp_code = :sp_code, geom = ST_GeomFromEWKT(:geom),
            updated_on = CURRENT_TIMESTAMP, updated_by = :updated_by
        WHERE polygon_id = :polygon_id
    """), {
        'polygon_id': polygon_id,
        'name': row['name'],
        'compartment': row['compartment'],
        'area_ha': row['area_ha'],
        'sp_code': row['sp_code'],
        'geom': row['geometry'].wkt if hasattr(row['geometry'], 'wkt') else None,
        'updated_by': current_user
    })

def insert_new_polygon(session, row, current_user):
    """Insert a new polygon record, setting proposal_id only if poly_type == 'BASE'."""
    proposal_id = row['proposal_id'] if row.get('poly_type') == 'BASE' else None

    session.execute(text("""
        INSERT INTO tmp_polygon (
            polygon_id, name, compartment, area_ha, sp_code, proposal_id, geom,
            created_on, created_by, updated_on, updated_by
        ) VALUES (
            :polygon_id, :name, :compartment, :area_ha, :sp_code, :proposal_id,
            ST_GeomFromEWKT(:geom),
            CURRENT_TIMESTAMP, :created_by, CURRENT_TIMESTAMP, :updated_by
        )
    """), {
        'polygon_id': row['polygon_id'],
        'name': row['name'],
        'compartment': row['compartment'],
        'area_ha': row['area_ha'],
        'sp_code': row['sp_code'],
        'proposal_id': proposal_id,
        'geom': row['geometry'].wkt if hasattr(row['geometry'], 'wkt') else None,
        'created_by': current_user,
        'updated_by': current_user
    })

def insert_duplicate_polygon(session, row, new_polygon_id, current_user):
    """Insert a duplicate polygon with a new polygon_id, setting proposal_id only if poly_type == 'BASE'."""
    proposal_id = row['proposal_id'] if row.get('poly_type') == 'BASE' else None

    session.execute(text("""
        INSERT INTO tmp_polygon (
            polygon_id, name, compartment, area_ha, sp_code, proposal_id, geom,
            created_on, created_by, updated_on, updated_by
        ) VALUES (
            :polygon_id, :name, :compartment, :area_ha, :sp_code, :proposal_id,
            ST_GeomFromEWKT(:geom),
            CURRENT_TIMESTAMP, :created_by, CURRENT_TIMESTAMP, :updated_by
        )
    """), {
        'polygon_id': new_polygon_id,
        'name': row['name'],
        'compartment': row['compartment'],
        'area_ha': row['area_ha'],
        'sp_code': row['sp_code'],
        'proposal_id': proposal_id,
        'geom': row['geometry'].wkt if hasattr(row['geometry'], 'wkt') else None,
        'created_by': current_user,
        'updated_by': current_user
    })

def update_existing_polygon(session, row, polygon_id, current_user):
    """Update an existing polygon record. proposal_id is set only if the current DB value is NULL."""
    proposal_id = row['proposal_id'] if row.get('poly_type') == 'BASE' else None

    session.execute(text("""
        UPDATE tmp_polygon
        SET name = :name, compartment = :compartment, area_ha = :area_ha,
            sp_code = :sp_code, geom = ST_GeomFromEWKT(:geom),
            proposal_id = COALESCE(proposal_id, :proposal_id),   -- only set if currently NULL
            updated_on = CURRENT_TIMESTAMP, updated_by = :updated_by
        WHERE polygon_id = :polygon_id
    """), {
        'polygon_id': polygon_id,
        'name': row['name'],
        'compartment': row['compartment'],
        'area_ha': row['area_ha'],
        'sp_code': row['sp_code'],
        'geom': row['geometry'].wkt if hasattr(row['geometry'], 'wkt') else None,
        'proposal_id': proposal_id,
        'updated_by': current_user
    })

def ___update_existing_polygon(session, row, polygon_id, current_user):
    """Update an existing polygon record, setting proposal_id only if poly_type == 'BASE'."""
    # Determine proposal_id based on poly_type
    proposal_id = row['proposal_id'] if row.get('poly_type') == 'BASE' else None
    #import ipdb; ipdb.set_trace()

    session.execute(text("""
        UPDATE tmp_polygon
        SET name = :name, compartment = :compartment, area_ha = :area_ha,
            sp_code = :sp_code, geom = ST_GeomFromEWKT(:geom),
            proposal_id = :proposal_id,
            updated_on = CURRENT_TIMESTAMP, updated_by = :updated_by
        WHERE polygon_id = :polygon_id
    """), {
        'polygon_id': polygon_id,
        'name': row['name'],
        'compartment': row['compartment'],
        'area_ha': row['area_ha'],
        'sp_code': row['sp_code'],
        'geom': row['geometry'].wkt if hasattr(row['geometry'], 'wkt') else None,
        'proposal_id': proposal_id,
        'updated_by': current_user
    })

# Keep the existing helper functions (they remain the same)
def create_audit_table(session):
    """Create audit table if it doesn't exist"""
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS tmp_polygon_audit (
            audit_id SERIAL PRIMARY KEY,
            polygon_id INTEGER,
            operation_type VARCHAR(10),
            operation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            operated_by VARCHAR(50),
            old_values JSONB,
            new_values JSONB
        )
    """))

def count_existing_polygon_id(session, polygon_id):
    """Count how many times a polygon_id exists in tmp_polygon"""
    result = session.execute(
        text("SELECT COUNT(*) FROM tmp_polygon WHERE polygon_id = :polygon_id"),
        {'polygon_id': polygon_id}
    )
    return result.scalar()

def is_duplicate_in_gdf(gdf, polygon_id, current_index):
    """Check if this polygon_id appears multiple times in the gdf"""
    total_count = (gdf['polygon_id'] == polygon_id).sum()
    first_occurrence_index = gdf[gdf['polygon_id'] == polygon_id].index[0]
    return current_index != first_occurrence_index

def get_next_polygon_id(session):
    """Get the next available polygon_id"""
    result = session.execute(text("""
        SELECT COALESCE(MAX(polygon_id), 0) + 1 FROM tmp_polygon
    """))
    return result.scalar()

def create_audit_records(session, before_state, after_state, current_user):
    """Create audit records for changes made - FIXED parameter syntax"""
    def convert_for_json(obj):
        """Convert datetime objects to strings for JSON serialization"""
        if isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj

    all_polygon_ids = set(before_state.keys()) | set(after_state.keys())

    for polygon_id in all_polygon_ids:
        before = before_state.get(polygon_id)
        after = after_state.get(polygon_id)

        # Convert datetime objects before JSON serialization
        before_converted = convert_for_json(before) if before else None
        after_converted = convert_for_json(after) if after else None

        if before is None and after is not None:
            # New record
            session.execute(text("""
                INSERT INTO tmp_polygon_audit
                (polygon_id, operation_type, operated_by, new_values)
                VALUES (:polygon_id, 'INSERT', :operated_by, :new_values)
            """), {
                'polygon_id': polygon_id,
                'operated_by': current_user,
                'new_values': json.dumps(after_converted) if after_converted else '{}'
            })
        elif before is not None and after is not None:
            # Updated record
            if before != after:
                session.execute(text("""
                    INSERT INTO tmp_polygon_audit
                    (polygon_id, operation_type, operated_by, old_values, new_values)
                    VALUES (:polygon_id, 'UPDATE', :operated_by, :old_values, :new_values)
                """), {
                    'polygon_id': polygon_id,
                    'operated_by': current_user,
                    'old_values': json.dumps(before_converted) if before_converted else '{}',
                    'new_values': json.dumps(after_converted) if after_converted else '{}'
                })

# Usage example
def main():
    # Assuming you have your gdf_result and engine
    engine = create_engine('postgresql://user:password@localhost/dbname')

    # Call the function - now returns two values
    operations_summary, gdf_result_with_new_ids = write_gdf_to_tmp_polygon(
        gdf_result=gdf_result,
        engine=engine,
        current_user="your_username"
    )

    print("Operation summary:", operations_summary)
    print("Updated GeoDataFrame with new IDs:")
    print(gdf_result_with_new_ids[['polygon_id', 'poly_id_new', 'poly_type']])  # Show the ID mapping

    # You can now use gdf_result_with_new_ids which contains the poly_id_new column
    return gdf_result_with_new_ids

if __name__ == "__main__":
    gdf_with_new_ids = main()
