import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection
from app.schemas.form106.form106_update_schema import Form106UpdateRequest
from app.utils.form106_helper import (
    get_week_ending_date,
    is_valid_date,
    form106_update_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form106",
    tags=["Form106"]
)


@router.put("/update")
def csa_form106_update(request: Form106UpdateRequest):

    conn = None

    try:

        # Validate Identity
        if request.def_id is None:
            return {
                "return_value": 1,
                "error_message": "Invalid ID"
            }

        # Validate Store
        if (
            request.def_store is None
            or str(request.def_store).strip() == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        # Validate Form Type
        if request.def_form_type != 6:
            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        # Validate Department
        if (
            request.def_department is None
            or str(request.def_department).strip() == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Department"
            }

        # Validate User

        if (
            not request.def_user
            or request.def_user.strip() == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid User"
            }

        # Validate Desc 1

        if (
            not request.def_descriptor_1
            or request.def_descriptor_1.strip() == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Description"
            }

        # validate amount
        if request.def_amount_2 is None:
            return {
                "return_value": 1,
                "error_message": "Invalid Expense Amount"
            }

        with DBConnection() as conn:
            with conn.cursor() as cur:

                # Get Store Configuration
                cur.execute("""
                    SELECT
                        sc_eow_last_run
                    FROM retail_accounting.store_configuration
                    WHERE tenant_id=%s
                    AND sc_store=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_store
                ))

                row = cur.fetchone()

                if not row or row[0] is None:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                week_ending_date = get_week_ending_date(
                    row[0].date()
                )

                # Validate Date
                if not is_valid_date(
                    request.def_date.date(),
                    week_ending_date
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                 # Check record exists
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

                count = cur.fetchone()[0]

                if count == 0:
                    return {
                        "return_value": 1,
                        "error_message": "Identity Not Found"
                    }

                # Fetch existing record
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
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
                ))

                existing = cur.fetchone()

                (
                    old_def_store,
                    old_def_date,
                    old_def_form_type,
                    old_def_department,
                    old_def_user,
                    old_def_descriptor_1,
                    old_def_descriptor_2,
                    old_def_amount_2
                ) = existing

                # Validate store matches existing record
                if old_def_store != request.def_store:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                # Validate form type matches existing record
                if old_def_form_type != request.def_form_type:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Form Type"
                    }

                # Fetch new department description
                cur.execute("""
                    SELECT d_description
                    FROM retail_accounting.departments
                    WHERE d_id=%s
                """,
                (
                    request.def_department,
                ))

                dept = cur.fetchone()
                d_description = dept[0] if dept else ""

                # Fetch old department description
                cur.execute("""
                    SELECT d_description
                    FROM retail_accounting.departments
                    WHERE d_id=%s
                """,
                (
                    old_def_department,
                ))

                old_dept = cur.fetchone()
                old_d_description = old_dept[0] if old_dept else ""

                                # Update form106 record
                cur.execute("""
                    UPDATE retail_accounting.data_entry_forms
                    SET
                        def_date=%s,
                        def_department=%s,
                        def_user=%s,
                        def_descriptor_1=%s,
                        def_descriptor_2=%s,
                        def_amount_2=%s
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    request.def_date,
                    request.def_department,
                    request.def_user,
                    request.def_descriptor_1,
                    request.def_descriptor_2,
                    request.def_amount_2,
                    str(request.tenant_id),
                    request.def_id
                ))

                # Check update success
                if cur.rowcount == 0:
                    conn.rollback()

                    return {
                        "return_value": 1,
                        "error_message": "Update Failed"
                    }

                 # Prepare Old Record
                old_record = {
                    "date": old_def_date,
                    "department": old_def_department,
                    "user": old_def_user,
                    "descriptor_1": old_def_descriptor_1,
                    "descriptor_2": old_def_descriptor_2,
                    "amount": old_def_amount_2
                }

                # Prepare New Record
                new_record = {
                    "date": request.def_date,
                    "department": request.def_department,
                    "user": request.def_user,
                    "descriptor_1": request.def_descriptor_1,
                    "descriptor_2": request.def_descriptor_2,
                    "amount": request.def_amount_2
                }

                 # Insert Update Audit
                form106_update_audit(
                    cur=cur,
                    tenant_id=request.tenant_id,
                    store=request.def_store,
                    date_value=request.def_date,
                    form_type=request.def_form_type,
                    user=request.def_user,
                    old_record=old_record,
                    new_record=new_record,
                    old_department_description=old_d_description,
                    new_department_description=d_description
                )

                # Commit Transaction
                conn.commit()

                return {
                    "return_value": 0,
                    "error_message": "",
                    "message": "Form106 updated successfully."
                }

    except Exception as e:

        if conn:
            conn.rollback()

        logger.exception(
            "Error in Form106 Update"
        )

        return {
            "return_value": 1,
            "error_message": f"Update Failed: {str(e)}"
        }

                