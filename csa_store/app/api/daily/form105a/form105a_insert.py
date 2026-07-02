import logging

from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form105a.form105a_insert_schema import (
    Form105AInsertRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form105a_helper import (
    update_dsc_with_form105a,
    insert_form105a_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form105a",
    tags=["Form105A"]
)


@router.post("/insert")
def form105a_insert(
        request: Form105AInsertRequest):
    """
    Equivalent of:

    csa_Form105a_Insert
    """

    conn = None

    try:

        #
        # VALIDATIONS
        #

        if request.def_store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if request.def_form_type != 4:

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

        if (
            request.def_descriptor_2 is None
            or
            request.def_descriptor_2.strip() == ""
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid Account Number"
            }

        if (
            request.def_descriptor_3 is None
            or
            request.def_descriptor_3.strip() == ""
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid Payment Type"
            }

        if request.def_amount_2 is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store Credit"
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
                # INSERT
                #

                cur.execute("""
                    INSERT INTO
                    retail_accounting.data_entry_forms
                    (
                        tenant_id,
                        def_store,
                        def_date,
                        def_form_type,
                        def_department,
                        def_user,
                        def_descriptor_1,
                        def_descriptor_2,
                        def_descriptor_3,
                        def_descriptor_4,
                        def_amount_1,
                        def_amount_2,
                        def_retail_acct_update_flag
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        NULL,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        0,
                        %s,
                        'N'
                    )
                    RETURNING def_id
                """,
                (
                    str(request.tenant_id),
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_user,
                    request.def_descriptor_1,
                    request.def_descriptor_2,
                    request.def_descriptor_3,
                    request.def_descriptor_4,
                    request.def_amount_2
                ))

                identity = cur.fetchone()[0]

                #
                # UPDATE DSC
                #

                update_dsc_with_form105a(
                    cur,
                    request.def_store,
                    week_ending_date
                )

                conn.commit()

                #
                # AUDIT
                #

                insert_form105a_audit(
                    cur,
                    request.tenant_id,
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_user,
                    request.def_amount_2,
                    identity
                )

                conn.commit()

                return {
                    "return_value": 0,
                    "id": identity
                }

    except Exception as ex:

        if conn:
            conn.rollback()

        logger.exception(
            "Error in Form105A Insert"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }