import logging

from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.form105b.form105b_update_schema import (
    Form105BUpdateRequest
)

from app.utils.form98_helper import (
    get_week_ending_date
)

from app.utils.form105b_helper import (
    update_dsc_with_form105b,
    insert_form105b_update_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form105b",
    tags=["Form105B"]
)


@router.put("/update")
def form105b_update(
        request: Form105BUpdateRequest):
    """
    Equivalent of:

    csa_Form105b_Update
    """

    conn = None

    try:

        #
        # VALIDATIONS
        #

        if request.def_id is None:

            return {
                "return_value": 1,
                "error_message": "Invalid ID"
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

        if (
            request.def_descriptor_1 is None
            or
            request.def_descriptor_1.strip() == ""
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid Customer Name"
            }

        if request.def_amount_2 is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store Charges"
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
                # CHECK RECORD EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id=%s
                """,
                (request.def_id,))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 1,
                        "error_message": "Identity Not Found"
                    }

                #
                # FETCH OLD VALUES
                #

                cur.execute("""
                    SELECT
                        def_store,
                        def_date,
                        def_form_type,
                        def_user,
                        def_descriptor_1,
                        def_descriptor_2,
                        def_descriptor_3,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id=%s
                """,
                (
                    request.def_id,
                ))

                old_row = cur.fetchone()

                (
                    old_store,
                    old_date,
                    old_form_type,
                    old_user,
                    old_desc1,
                    old_desc2,
                    old_desc3,
                    old_amount
                ) = old_row

                if old_store != request.def_store:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                if old_form_type != request.def_form_type:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Form Type"
                    }

                #
                # UPDATE
                #

                cur.execute("""
                    UPDATE retail_accounting.data_entry_forms
                    SET
                        def_date=%s,
                        def_user=%s,
                        def_descriptor_1=%s,
                        def_descriptor_2=%s,
                        def_descriptor_3=%s,
                        def_amount_2=%s
                    WHERE def_id=%s
                """,
                (
                    request.def_date,
                    request.def_user,
                    request.def_descriptor_1,
                    request.def_descriptor_2,
                    request.def_descriptor_3,
                    request.def_amount_2,
                    request.def_id
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
                # AUDITS
                #

                if old_date.date() != request.def_date:

                    insert_form105b_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Date Changed From: {old_date.strftime('%m/%d/%y')} To: {request.def_date.strftime('%m/%d/%y')}"
                    )

                if old_user != request.def_user:

                    insert_form105b_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"User Changed From: {old_user} To: {request.def_user}"
                    )

                if old_desc1 != request.def_descriptor_1:

                    insert_form105b_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Descriptor 1 Changed From: {old_desc1} To: {request.def_descriptor_1}"
                    )

                if old_desc2 != request.def_descriptor_2:

                    insert_form105b_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Descriptor 2 Changed From: {old_desc2} To: {request.def_descriptor_2}"
                    )

                if old_desc3 != request.def_descriptor_3:

                    insert_form105b_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Descriptor 3 Changed From: {old_desc3} To: {request.def_descriptor_3}"
                    )

                if float(old_amount) != float(request.def_amount_2):

                    insert_form105b_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Amount 2 Changed From: {old_amount} To: {request.def_amount_2}"
                    )

                conn.commit()

                return {
                    "return_value": 0,
                    "message": "Record Updated Successfully"
                }

    except Exception as ex:

        if conn:
            conn.rollback()

        logger.exception(
            "Error in Form105B Update"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }