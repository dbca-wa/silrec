from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, and_
from sqlalchemy.orm import sessionmaker

from django.db import IntegrityError, transaction
from silrec.components.forest_blocks.models import Cohort
from silrec.utils.create_audit_log import AuditLogger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_cohort_record(obj_code: str, op_id: int, year: int, target_ba: int, regen_method: str, user_id: int, proposal_id: int, int=None) -> int | None:
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
        cohort_qs = Cohort.objects.filter(
            obj_code=obj_code,
            op_id=op_id,
            op_date=op_date,
            target_ba_m2ha=target_ba_float,
            regen_method_id=regen_method #' %', # FK req'd
        )
        cohort_obj_orig = cohort_qs[0]

        if len(cohort_qs) == 0:
            cohort_obj = Cohort.objects.create(
                obj_code=obj_code,
                op_id=op_id,
                op_date=op_date,
                target_ba_m2ha=target_ba_float,
                regen_method_id=regen_method #' %', # FK req'd
                # No extra defaults needed because we're providing all field values.
            )

            al = AuditLogger(Cohort, cohort_obj, 'INSERT', user_id, proposal_id, obj_orig, obj)
            logger.info(f"Successful INSERT cohort record with ID: {cohort_id}")
        else:
            al = AuditLogger(Cohort, cohort_obj, 'UPDATE', user_id, proposal_id, cohort_obj_orig, obj)
            logger.info(f"Successful UPDATE cohort record with ID: {cohort_id}")

        return cohort_obj.cohort_id

    except IntegrityError as e:
        # Handle any database integrity errors (e.g., duplicate key despite check)
        logger.error(f"Database integrity error creating cohort record: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating cohort record: {e}")
        return None


