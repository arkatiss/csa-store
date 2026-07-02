import logging
from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form103.form103_delete_request import (
    Form103DeleteRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form103_helper import (
    update_dsc_with_form103,
    insert_form103_delete_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form103",
    tags=["Form103"]
)


@router.delete("/delete")
def form103_delete(
        request: Form103DeleteRequest):

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # VALIDATIONS
                #

                if request.def_id is None:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Identity"
                    }

                if request.def_store is None:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                week_ending_date = get_week_ending_date(
                    cur,
                    request.def_store
                )

                if (
                    request.def_date <
                    (week_ending_date - timedelta(days=7))
                    or
                    request.def_date >
                    (week_ending_date + timedelta(days=1))
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                if request.def_form_type != 2:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Form Type"
                    }

                if request.def_department is None:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Department"
                    }

                if not request.def_user:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid User"
                    }

                #
                # FETCH ORIGINAL RECORD
                #

                cur.execute("""
                    SELECT
                        def_store,
                        def_date,
                        def_form_type,
                        def_department,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id=%s
                """,
                (
                    request.def_id,
                ))

                row = cur.fetchone()

                if not row:

                    return {
                        "return_value": 1,
                        "error_message": "Identity Not Found"
                    }

                (
                    db_store,
                    db_date,
                    db_form_type,
                    db_department,
                    db_amount
                ) = row

                #
                # VALIDATE DB VALUES
                #

                if db_store != request.def_store:

                    return {
                        "return_value": 1,
                        "error_message": "Wrong Store"
                    }

                if db_date.date() != request.def_date:

                    return {
                        "return_value": 1,
                        "error_message": "Wrong Date"
                    }

                if db_form_type != request.def_form_type:

                    return {
                        "return_value": 1,
                        "error_message": "Wrong Form Type"
                    }

                if db_department != request.def_department:

                    return {
                        "return_value": 1,
                        "error_message": "Wrong Department"
                    }

                #
                # DEPARTMENT DESCRIPTION
                #

                cur.execute("""
                    SELECT d_description
                    FROM retail_accounting.departments
                    WHERE d_id=%s
                """,
                (
                    request.def_department,
                ))

                dept_row = cur.fetchone()

                department_description = (
                    dept_row[0]
                    if dept_row
                    else "Unknown"
                )

                #
                # DELETE
                #

                cur.execute("""
                    DELETE
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id=%s
                """,
                (
                    request.def_id,
                ))

                if cur.rowcount == 0:

                    conn.rollback()

                    return {
                        "return_value": 1,
                        "error_message": "Delete Failed"
                    }

                #
                # RECALCULATE TOTALS
                #

                update_dsc_with_form103(
                    cur,
                    request.def_store,
                    request.def_department,
                    week_ending_date
                )

                #
                # AUDIT
                #

                comment = (
                    f"Department - "
                    f"{department_description}, "
                    f"Amount - "
                    f"{db_amount}, "
                    f"Identity - "
                    f"{request.def_id}"
                )

                insert_form103_delete_audit(
                    cur,
                    request.tenant_id,
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_user,
                    comment
                )

                conn.commit()

                return {
                    "return_value": 0
                }

    except Exception as ex:

        logger.exception(ex)

        return {
            "return_value": 1,
            "error_message": str(ex)
        }