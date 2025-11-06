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
    and create audit trail.

    Args:
        gdf_result: GeoDataFrame with polygon data
        engine: SQLAlchemy engine
        current_user: User performing the operation

    Returns:
        dict: Summary of operations performed
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    Session = sessionmaker(bind=engine)
    session = Session()

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
            'updated_polygon_ids': []
        }

        # Process each row in the GeoDataFrame
        for idx, row in gdf_result.iterrows():
            polygon_id = row['polygon_id']

            # Check if this polygon_id already exists in tmp_polygon
            existing_count = count_existing_polygon_id(session, polygon_id)

            if existing_count == 0:
                # New polygon_id - insert as is
                insert_new_polygon(session, row, current_user)
                operations_summary['new_records'] += 1
                operations_summary['new_polygon_ids'].append(polygon_id)
                logger.info(f"Inserted new record with polygon_id: {polygon_id}")

            else:
                # Polygon_id exists - check if we need to create a new record
                if is_duplicate_in_gdf(gdf_result, polygon_id, idx):
                    # This is a duplicate in the current gdf_result - create new record with new polygon_id
                    new_polygon_id = get_next_polygon_id(session)
                    insert_duplicate_polygon(session, row, new_polygon_id, current_user)
                    operations_summary['new_records'] += 1
                    operations_summary['new_polygon_ids'].append(new_polygon_id)
                    logger.info(f"Created duplicate record: {polygon_id} -> {new_polygon_id}")
                else:
                    # Update existing record
                    update_existing_polygon(session, row, polygon_id, current_user)
                    operations_summary['updated_records'] += 1
                    operations_summary['updated_polygon_ids'].append(polygon_id)
                    logger.info(f"Updated existing record with polygon_id: {polygon_id}")

        # Get final state and create audit records
        final_records = get_current_tmp_polygon_records(session)
        create_audit_records(session, current_records, final_records, current_user)

        session.commit()

        logger.info(f"Operation completed: {operations_summary}")
        return operations_summary

    except Exception as e:
        session.rollback()
        logger.error(f"Error writing to tmp_polygon: {e}")
        raise
    finally:
        session.close()

# Helper functions
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

def get_current_tmp_polygon_records(session):
    """Get current state of tmp_polygon table"""
    result = session.execute(text("""
        SELECT polygon_id, name, compartment, area_ha, sp_code, created_on, created_by
        FROM tmp_polygon
    """))
    return {row[0]: dict(row._mapping) for row in result}

def count_existing_polygon_id(session, polygon_id):
    """Count how many times a polygon_id exists in tmp_polygon"""
    result = session.execute(
        text("SELECT COUNT(*) FROM tmp_polygon WHERE polygon_id = :polygon_id"),
        {'polygon_id': polygon_id}
    )
    return result.scalar()

def is_duplicate_in_gdf(gdf, polygon_id, current_index):
    """Check if this polygon_id appears multiple times in the gdf"""
    # Count occurrences of this polygon_id in the entire gdf
    total_count = (gdf['polygon_id'] == polygon_id).sum()
    # Check if this is not the first occurrence
    first_occurrence_index = gdf[gdf['polygon_id'] == polygon_id].index[0]
    return current_index != first_occurrence_index

def get_next_polygon_id(session):
    """Get the next available polygon_id"""
    result = session.execute(text("""
        SELECT COALESCE(MAX(polygon_id), 0) + 1 FROM tmp_polygon
    """))
    return result.scalar()

def insert_new_polygon(session, row, current_user):
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

def insert_duplicate_polygon(session, row, new_polygon_id, current_user):
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

def update_existing_polygon(session, row, polygon_id, current_user):
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
            # New record - FIXED parameter syntax
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
            # Updated record - FIXED parameter syntax
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

#def create_audit_records(session, before_state, after_state, current_user):
#    """Create audit records for changes made - FIXED VERSION"""
#    all_polygon_ids = set(before_state.keys()) | set(after_state.keys())
#
#    for polygon_id in all_polygon_ids:
#        before = before_state.get(polygon_id)
#        after = after_state.get(polygon_id)
#
#        if before is None and after is not None:
#            # New record
#            session.execute(text("""
#                INSERT INTO tmp_polygon_audit
#                (polygon_id, operation_type, operated_by, new_values)
#                VALUES (:polygon_id, 'INSERT', :operated_by, :new_values)
#            """), {
#                'polygon_id': polygon_id,
#                'operated_by': current_user,
#                'new_values': json.dumps(after) if after else '{}'
#            })
#        elif before is not None and after is not None:
#            # Updated record - only log if there are actual changes
#            if before != after:
#                session.execute(text("""
#                    INSERT INTO tmp_polygon_audit
#                    (polygon_id, operation_type, operated_by, old_values, new_values)
#                    VALUES (:polygon_id, 'UPDATE', :operated_by, :old_values, :new_values)
#                """), {
#                    'polygon_id': polygon_id,
#                    'operated_by': current_user,
#                    'old_values': json.dumps(before) if before else '{}',
#                    'new_values': json.dumps(after) if after else '{}'
#                })

#def create_audit_records(session, before_state, after_state, current_user):
#    """Create audit records for changes made"""
#    all_polygon_ids = set(before_state.keys()) | set(after_state.keys())
#
#    for polygon_id in all_polygon_ids:
#        before = before_state.get(polygon_id)
#        after = after_state.get(polygon_id)
#
#        if before is None and after is not None:
#            # New record
#            session.execute(text("""
#                INSERT INTO tmp_polygon_audit
#                (polygon_id, operation_type, operated_by, new_values)
#                VALUES (:polygon_id, 'INSERT', :operated_by, :new_values)
#            """), {
#                'polygon_id': polygon_id,
#                'operated_by': current_user,
#                'new_values': str(after)
#            })
#        elif before is not None and after is not None:
#            # Updated record
#            session.execute(text("""
#                INSERT INTO tmp_polygon_audit
#                (polygon_id, operation_type, operated_by, old_values, new_values)
#                VALUES (:polygon_id, 'UPDATE', :operated_by, :old_values, :new_values)
#            """), {
#                'polygon_id': polygon_id,
#                'operated_by': current_user,
#                'old_values': str(before),
#                'new_values': str(after)
#            })

# Usage example
def main():
    # Assuming you have your gdf_result and engine
    engine = create_engine('postgresql://user:password@localhost/dbname')

    # Call the function
    result = write_gdf_to_tmp_polygon(
        gdf_result=gdf_result,
        engine=engine,
        current_user="your_username"
    )

    print("Operation summary:", result)

if __name__ == "__main__":
    main()
