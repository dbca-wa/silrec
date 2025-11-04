from django.db import connection, transaction


def create_temp_tables_django_models():
    """
    Create temporary tables using Django models

    from silrec.utils.create_temp_tables import create_temp_tables_django_models, clear_temp_tables_django
    create_temp_tables_django_models()
    clear_temp_tables_django()
    """
    from silrec.components.forest_blocks.models import Polygon, AssignChtToPly, Cohort

    with transaction.atomic():
        # Create temporary tables structure
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tmp_polygon AS TABLE polygon WITH NO DATA;
                CREATE TABLE IF NOT EXISTS tmp_assign_cht_to_ply AS TABLE assign_cht_to_ply WITH NO DATA;
                CREATE TABLE IF NOT EXISTS tmp_cohort AS TABLE cohort WITH NO DATA;
            """)

        # Copy data directly using raw SQL (more efficient and avoids primary key conflicts)
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO tmp_polygon SELECT * FROM polygon")
            cursor.execute("INSERT INTO tmp_assign_cht_to_ply SELECT * FROM assign_cht_to_ply")
            cursor.execute("INSERT INTO tmp_cohort SELECT * FROM cohort")

def clear_temp_tables_django():
    """
    Clear all tmp_* tables
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            DROP TABLE IF EXISTS tmp_polygon;
            DROP TABLE IF EXISTS tmp_assign_cht_to_ply;
            DROP TABLE IF EXISTS tmp_cohort;
        """)
