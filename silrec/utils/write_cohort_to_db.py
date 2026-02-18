from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

def create_cohort_record(engine, obj_code: str, op_id: int, year: int, target_ba: int):
    """
    Create a record in tmp_cohort table with obj_code, op_id, and op_date
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
        metadata = MetaData()
        tmp_cohort = Table('tmp_cohort', metadata, autoload_with=engine, schema='silrec')

        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Convert year to datetime (January 1st of the given year)
        op_date = datetime(year, 1, 1)

        # First, check if record already exists
        #import ipdb; ipdb.set_trace()
        existing_record = session.execute(
            tmp_cohort.select().where(
                and_(
                    tmp_cohort.c.obj_code == obj_code,
                    tmp_cohort.c.op_id == op_id,
                    tmp_cohort.c.op_date == op_date,
                    tmp_cohort.c.target_ba_m2ha == float(target_ba)
                )
            )
        ).first()

        if existing_record:
            cohort_id = existing_record.cohort_id
            logging.info(f"Record already exists with cohort_id: {cohort_id}")
            return cohort_id

        # If record doesn't exist, create it
        stmt = tmp_cohort.insert().values(
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

# Alternative version using SQLAlchemy ORM if you have a defined model:
def create_cohort_record_orm(session, obj_code: str, op_id: int, year: int):
    """
    Create a record using SQLAlchemy ORM approach - only if doesn't exist
    """
    try:
        # Assuming you have a Cohort model defined
        op_date = datetime(year, 1, 1)

        # Check if record already exists
        existing_cohort = session.query(Cohort).filter(
            and_(
                Cohort.obj_code == obj_code,
                Cohort.op_id == op_id,
                Cohort.op_date == op_date
            )
        ).first()

        if existing_cohort:
            logging.info(f"Record already exists with cohort_id: {existing_cohort.cohort_id}")
            return existing_cohort.cohort_id

        # Create new record
        cohort = Cohort(
            obj_code=obj_code,
            op_id=op_id,
            op_date=op_date
        )

        session.add(cohort)
        session.commit()

        logging.info(f"Successfully created cohort record with ID: {cohort.cohort_id}")
        return cohort.cohort_id

    except Exception as e:
        logging.error(f"Error creating cohort record: {e}")
        session.rollback()
        return None

