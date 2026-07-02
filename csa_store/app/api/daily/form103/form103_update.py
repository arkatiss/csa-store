import logging
from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form103.form103_update_request import (
    Form103UpdateRequest
)

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

from app.utils.daily.form103_helper import (
    update_dsc_with_form103,
    insert_form103_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form103",
    tags=["Form103"]
)

@router.put("/update")
def form103_update(
        request: Form103UpdateRequest):

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

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

                if not request.def_descriptor_1:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Vendor/Item"
                    }

                if request.def_amount_2 is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Cost"
                    }

                #
                # ID EXISTS ?
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
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
                        def_amount_1,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
                ))

                old_row = cur.fetchone()

                (
                    old_store,
                    old_date,
                    old_form_type,
                    old_department,
                    old_user,
                    old_desc1,
                    old_desc2,
                    old_amt1,
                    old_amt2
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
                        def_department=%s,
                        def_user=%s,
                        def_descriptor_1=%s,
                        def_descriptor_2=%s,
                        def_amount_1=%s,
                        def_amount_2=%s,
                        updated_at=CURRENT_TIMESTAMP,
                        updated_by=%s
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    request.def_date,
                    request.def_department,
                    request.def_user,
                    request.def_descriptor_1,
                    request.def_descriptor_2,
                    request.def_amount_1,
                    request.def_amount_2,
                    request.def_user,
                    str(request.tenant_id),
                    request.def_id
                ))

                #
                # RECALCULATE CURRENT DEPARTMENT
                #

                update_dsc_with_form103(
                    cur,
                    request.def_store,
                    request.def_department,
                    week_ending_date
                )

                #
                # RECALCULATE OLD DEPARTMENT
                #

                if old_department != request.def_department:

                    update_dsc_with_form103(
                        cur,
                        request.def_store,
                        old_department,
                        week_ending_date
                    )

                conn.commit()

                #
                # AUDITS
                #

                if old_date != request.def_date:

                    insert_form103_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Date Changed From: "
                        f"{old_date} To: "
                        f"{request.def_date}"
                    )

                if old_department != request.def_department:

                    cur.execute("""
                        SELECT d_description
                        FROM retail_accounting.departments
                        WHERE d_id=%s
                    """,
                    (request.def_department,))

                    new_dept = cur.fetchone()[0]

                    cur.execute("""
                        SELECT d_description
                        FROM retail_accounting.departments
                        WHERE d_id=%s
                    """,
                    (old_department,))

                    old_dept = cur.fetchone()[0]

                    insert_form103_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Department Changed From: "
                        f"{old_dept} To: "
                        f"{new_dept}"
                    )

                if old_user != request.def_user:

                    insert_form103_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"User Changed From: "
                        f"{old_user} To: "
                        f"{request.def_user}"
                    )

                if old_desc1 != request.def_descriptor_1:

                    insert_form103_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Descriptor 1 Changed From: "
                        f"{old_desc1} To: "
                        f"{request.def_descriptor_1}"
                    )

                if old_desc2 != request.def_descriptor_2:

                    old_value = (
                        old_desc2
                        if old_desc2
                        else "Blank"
                    )

                    insert_form103_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Descriptor 2 Changed From: "
                        f"{old_value} To: "
                        f"{request.def_descriptor_2}"
                    )

                if old_amt1 != request.def_amount_1:

                    insert_form103_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Amount 1 Changed From: "
                        f"{old_amt1} To: "
                        f"{request.def_amount_1}"
                    )

                if old_amt2 != request.def_amount_2:

                    insert_form103_audit(
                        cur,
                        request.tenant_id,
                        request.def_store,
                        request.def_date,
                        request.def_form_type,
                        request.def_user,
                        f"Amount 2 Changed From: "
                        f"{old_amt2} To: "
                        f"{request.def_amount_2}"
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