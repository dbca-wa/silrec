from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, and_
from sqlalchemy.orm import sessionmaker

from django.db import IntegrityError, transaction
from silrec.components.forest_blocks.models import Cohort
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_cohort_record(obj_code: str, op_id: int, year: int, target_ba: int, regen_method: str) -> int | None:
    """
    Create a record in the cohort table using.
    Returns the cohort_id if the record exists or is created successfully,
    otherwise returns None.
    """
    try:
        op_date = datetime(year, 1, 1)
        target_ba_float = float(target_ba)

        # Use get_or_create to either fetch the existing record or create a new one.
        # The lookup uses all fields that define uniqueness.
        #import ipdb; ipdb.set_trace()
        cohort_obj, created = Cohort.objects.get_or_create(
            obj_code=obj_code,
            op_id=op_id,
            op_date=op_date,
            target_ba_m2ha=target_ba_float,
            regen_method_id=regen_method #' %', # FK req'd
            # No extra defaults needed because we're providing all field values.
        )

        cohort_id = cohort_obj.cohort_id
        if created:
            logger.info(f"Successfully created cohort record with ID: {cohort_id}")
        else:
            logger.info(f"Record already exists with cohort_id: {cohort_id}")

        return cohort_id

    except IntegrityError as e:
        # Handle any database integrity errors (e.g., duplicate key despite check)
        logger.error(f"Database integrity error creating cohort record: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating cohort record: {e}")
        return None

def _create_cohort_record(engine, obj_code: str, op_id: int, year: int, target_ba: int):
    """
    Create a record in cohort table with obj_code, op_id, and op_date
    only if a record with these values doesn't already exist.

    Args:
        engine: SQLAlchemy engine instance
        obj_code (str): 20-character object code
        op_id (int): Operation ID
        year (int): Year for op_date (will be converted to datetime with Jan 1)

    Returns:
        int: The created cohort_id, or existing cohort_id, or None if failed
    """
    try:
        # Reflect the existing table
        #import ipdb; ipdb.set_trace()
        metadata = MetaData()
        cohort = Table('cohort', metadata, autoload_with=engine, schema='silrec')

        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Convert year to datetime (January 1st of the given year)
        op_date = datetime(year, 1, 1)

        # First, check if record already exists
        #import ipdb; ipdb.set_trace()
        existing_record = session.execute(
            cohort.select().where(
                and_(
                    cohort.c.obj_code == obj_code,
                    cohort.c.op_id == op_id,
                    cohort.c.op_date == op_date,
                    cohort.c.target_ba_m2ha == float(target_ba)
                )
            )
        ).first()

        if existing_record:
            cohort_id = existing_record.cohort_id
            logging.info(f"Record already exists with cohort_id: {cohort_id}")
            return cohort_id

        # If record doesn't exist, create it
        stmt = cohort.insert().values(
            obj_code=obj_code,
            op_id=op_id,
            op_date=op_date,
            target_ba_m2ha=float(target_ba)
        )

        # Execute and get the inserted cohort_id
        result = session.execute(stmt)
        cohort_id = result.inserted_primary_key[0]

        # Commit the transaction
        session.commit()

        logging.info(f"Successfully created cohort record with ID: {cohort_id}")
        return cohort_id

    except Exception as e:
        logging.error(f"Error creating cohort record: {e}")
        session.rollback()
        return None
    finally:
        session.close()


