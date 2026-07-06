import logging

from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form105b.form105b_delete_schema import (
    Form105BDeleteRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form105b_helper import (
    update_dsc_with_form105b,
    insert_form105b_delete_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form105b",
    tags=["Form105B"]
)


@router.delete("/delete")
def form105b_delete(
        request: Form105BDeleteRequest):
    """
    Equivalent of:

    csa_Form105b_Delete
    """

    conn = None

    try:

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

        if request.def_form_type != 5:

            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        if (
            request.def_user is None
            or
            request.def_user.strip() == ""
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid User"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # WEEK ENDING DATE
                #

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

                #
                # FETCH RECORD
                #

                cur.execute("""
                    SELECT
                        def_store,
                        def_date,
                        def_form_type,
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
                    i_def_store,
                    i_def_date,
                    i_def_form_type,
                    i_def_amount_2
                ) = row

                #
                # VALIDATE EXISTING VALUES
                #

                if i_def_store != request.def_store:

                    return {
                        "return_value": 1,
                        "error_message": "Wrong Store"
                    }

                if i_def_date.date() != request.def_date:

                    return {
                        "return_value": 1,
                        "error_message": "Wrong Date"
                    }

                if i_def_form_type != request.def_form_type:

                    return {
                        "return_value": 1,
                        "error_message": "Wrong Form Type"
                    }

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

                #
                # UPDATE DSC
                #

                update_dsc_with_form105b(
                    cur,
                    request.def_store,
                    week_ending_date
                )

                conn.commit()

                #
                # AUDIT
                #

                insert_form105b_delete_audit(
                    cur,
                    request.tenant_id,
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_user,
                    i_def_amount_2,
                    request.def_id
                )

                conn.commit()

                logger.info(
                    f"Form105B deleted successfully. "
                    f"ID={request.def_id}"
                )

                return {
                    "return_value": 0,
                    "message": "Record Deleted Successfully"
                }

    except Exception as ex:

        if conn:
            conn.rollback()

        logger.exception(
            "Error in Form105B Delete"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }