import logging

from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form111.form111_delete_schema import (
    Form111DeleteRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form111_helper import (
    update_dsc_with_form111,
    insert_form111_delete_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form111",
    tags=["Form111"]
)


@router.delete("/delete")
def form111_delete(
        request: Form111DeleteRequest):
    """
    Equivalent of:

    csa_Form111_Delete
    """

    try:

        #
        # VALIDATIONS
        #

        if not request.def_id:
            return {
                "return_value": 1,
                "error_message": "Invalid Identity"
            }

        if not request.def_store:
            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if request.def_form_type != 7:
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
                # FETCH ROW
                #

                cur.execute("""
                    SELECT
                        def_store,
                        def_date,
                        def_form_type,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
                ))

                row = cur.fetchone()

                if not row:
                    return {
                        "return_value": 1,
                        "error_message": "Identity Not Found"
                    }

                db_store = row[0]
                db_date = row[1]
                db_form_type = row[2]
                db_amount_2 = row[3]

                #
                # VALIDATIONS
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

                #
                # DELETE
                #

                cur.execute("""
                    DELETE FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
                ))

                if cur.rowcount == 0:
                    conn.rollback()

                    return {
                        "return_value": 1,
                        "error_message": "Delete Failed"
                    }

                #
                # UPDATE DSC
                #

                update_dsc_with_form111(
                    cur,
                    request.tenant_id,
                    request.def_store,
                    week_ending_date
                )

                conn.commit()

                #
                # AUDIT
                #

                insert_form111_delete_audit(
                    cur,
                    request.tenant_id,
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_user,
                    db_amount_2,
                    request.def_id
                )

                conn.commit()

                return {
                    "return_value": 0,
                    "message": "Form111 Deleted Successfully"
                }

    except Exception as ex:

        logger.exception(
            "Error in Form111 Delete"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }