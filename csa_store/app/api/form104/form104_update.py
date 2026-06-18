import logging

from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.form104.form104_update_request import (
    Form104UpdateRequest
)

from app.utils.form98_helper import (
    get_week_ending_date
)

from app.utils.form104_helper import (
    update_dsc_with_form104,
    insert_form104_update_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form104",
    tags=["Form104"]
)

@router.put("/update")
def form104_update(
        request: Form104UpdateRequest):
    """
    Equivalent of:

    csa_Form104_Update
    """

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

        if request.def_form_type != 3:

            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        if not request.def_user:

            return {
                "return_value": 1,
                "error_message": "Invalid User"
            }

        if not request.def_descriptor_1:

            return {
                "return_value": 1,
                "error_message": "Invalid Description"
            }

        if request.def_amount_2 is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Cost"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                week_ending_date = get_week_ending_date(
                    cur,
                    request.def_store
                )

                #
                # INVALID DATE
                #

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
                # ID EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id=%s
                """,
                (
                    request.def_id,
                ))

                if cur.fetchone()[0] == 0:

                    return {
                        "return_value": 1,
                        "error_message": "Identity Not Found"
                    }

                #
                # OLD VALUES
                #

                cur.execute("""
                    SELECT
                        def_store,
                        def_date,
                        def_form_type,
                        def_department,
                        def_user,
                        def_descriptor_1,
                        def_descriptor_2,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id=%s
                """,
                (
                    request.def_id,
                ))

                old_row = cur.fetchone()

                old_store = old_row[0]
                old_date = old_row[1]
                old_form_type = old_row[2]
                old_department = old_row[3]
                old_user = old_row[4]
                old_desc1 = old_row[5]
                old_desc2 = old_row[6]
                old_amount2 = old_row[7]

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

                cur.execute("""
                    UPDATE retail_accounting.data_entry_forms
                    SET
                        def_date=%s,
                        def_department=%s,
                        def_user=%s,
                        def_descriptor_1=%s,
                        def_descriptor_2=%s,
                        def_amount_2=%s,
                        updated_by=%s
                    WHERE def_id=%s
                """,
                            (
                                request.def_date,
                                request.def_department,
                                request.def_user,
                                request.def_descriptor_1,
                                request.def_descriptor_2,
                                request.def_amount_2,
                                request.def_user,
                                request.def_id
                            ))

                update_dsc_with_form104(
                    cur,
                    request.def_store,
                    week_ending_date
                )

                conn.commit()

                if old_date != request.def_date:
                    insert_form104_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        (
                            f"Date Changed From: "
                            f"{old_date} "
                            f"To: "
                            f"{request.def_date}"
                        )
                    )

                if old_department != request.def_department:
                    cur.execute("""
                        SELECT d_description
                        FROM retail_accounting.departments
                        WHERE d_id=%s
                    """,
                                (
                                    request.def_department,
                                ))

                    new_dept = cur.fetchone()[0]

                    cur.execute("""
                        SELECT d_description
                        FROM retail_accounting.departments
                        WHERE d_id=%s
                    """,
                                (
                                    old_department,
                                ))

                old_dept = cur.fetchone()[0]

                insert_form104_update_audit(
                    cur,
                    request.tenant_id,
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_user,
                    (
                        f"Department Changed From: "
                        f"{old_dept} "
                        f"To: "
                        f"{new_dept}"
                    )
                )


                if old_user != request.def_user:
                    insert_form104_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        (
                            f"User Changed From: "
                            f"{old_user} "
                            f"To: "
                            f"{request.def_user}"
                        )
                    )


                if old_desc1 != request.def_descriptor_1:
                    insert_form104_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        (
                            f"Descriptor 1 Changed From: "
                            f"{old_desc1} "
                            f"To: "
                            f"{request.def_descriptor_1}"
                        )
                    )


                if old_desc2 != request.def_descriptor_2:
                    insert_form104_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        (
                            f"Descriptor 2 Changed From: "
                            f"{old_desc2 or 'Blank'} "
                            f"To: "
                            f"{request.def_descriptor_2}"
                        )
                    )


                if old_amount2 != request.def_amount_2:
                    insert_form104_update_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        (
                            f"Amount 2 Changed From: "
                            f"{old_amount2} "
                            f"To: "
                            f"{request.def_amount_2}"
                        )
                    )

                conn.commit()

                return {
                    "return_value": 0
                }

    except Exception as ex:

        logger.exception(
            "Error in Form104 Update"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }