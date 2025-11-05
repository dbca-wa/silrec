from django.db import connection, transaction

def create_temp_tables_django_models():
    """
    Create temporary tables using Django models
    """
    from silrec.components.forest_blocks.models import Polygon, AssignChtToPly, Cohort

    with transaction.atomic():
        # Create temporary tables structure WITH primary keys
        with connection.cursor() as cursor:
            cursor.execute("""
                -- Create temporary tables with proper primary key constraints
                CREATE TABLE IF NOT EXISTS tmp_polygon (LIKE polygon INCLUDING ALL);
                CREATE TABLE IF NOT EXISTS tmp_assign_cht_to_ply (LIKE assign_cht_to_ply INCLUDING ALL);
                CREATE TABLE IF NOT EXISTS tmp_cohort (LIKE cohort INCLUDING ALL);
            """)

        # Copy data directly using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO tmp_polygon SELECT * FROM polygon")
            cursor.execute("INSERT INTO tmp_assign_cht_to_ply SELECT * FROM assign_cht_to_ply")
            cursor.execute("INSERT INTO tmp_cohort SELECT * FROM cohort")

        # Add foreign key constraints to temporary tables
        with connection.cursor() as cursor:
            # First, drop any existing foreign key constraints that might reference original tables
            cursor.execute("""
                ALTER TABLE tmp_assign_cht_to_ply
                DROP CONSTRAINT IF EXISTS tmp_assign_cht_to_ply_polygon_id_fkey,
                DROP CONSTRAINT IF EXISTS tmp_assign_cht_to_ply_cohort_id_fkey;
            """)

            # Add foreign key constraints that reference the temporary tables
            cursor.execute("""
                ALTER TABLE tmp_assign_cht_to_ply
                ADD CONSTRAINT tmp_assign_cht_to_ply_polygon_fk
                FOREIGN KEY (polygon_id) REFERENCES tmp_polygon(polygon_id);

                ALTER TABLE tmp_assign_cht_to_ply
                ADD CONSTRAINT tmp_assign_cht_to_ply_cohort_fk
                FOREIGN KEY (cohort_id) REFERENCES tmp_cohort(cohort_id);
            """)

def clear_temp_tables_django():
    """
    Clear all tmp_* tables
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            DROP TABLE IF EXISTS tmp_assign_cht_to_ply CASCADE;
            DROP TABLE IF EXISTS tmp_polygon CASCADE;
            DROP TABLE IF EXISTS tmp_cohort CASCADE;
        """)

