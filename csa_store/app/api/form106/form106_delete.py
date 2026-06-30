import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection
from app.schemas.form106.form106_delete_schema import Form106DeleteRequest
from app.utils.form106_helper import (
    get_week_ending_date,
    is_valid_date,
    delete_form106_audit
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form106",
    tags=["Form106"]
)


@router.delete("/delete")
def csa_form106_delete(request: Form106DeleteRequest):
    conn = None

    try:

        # Validate Identity
        if request.def_id is None:
            return {
                "return_value": 1,
                "error_message": "Invalid Identity"
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

        with DBConnection() as conn:
            with conn.cursor() as cur:

            
                # Get Week Ending Date
                cur.execute("""
                    SELECT sc_eow_last_run
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

                week_ending_date = get_week_ending_date(row[0].date())

                # Validate Date
                if not is_valid_date(
                    request.def_date.date(),
                    week_ending_date
                ):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

        
                # Fetch Existing Record
                cur.execute("""
                    SELECT
                        def_store,
                        def_date,
                        def_form_type,
                        def_department,
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

                if not existing:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Identity"
                    }

                (
                    db_store,
                    db_date,
                    db_form_type,
                    db_department,
                    db_amount
                ) = existing


                # Verify Existing Record
                if db_store != request.def_store:
                    return {
                        "return_value": 1,
                        "error_message": "Wrong Store"
                    }

                if db_date.date() != request.def_date.date():
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

                # Department Description
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

                # Delete Record
                cur.execute("""
                    DELETE
                    FROM retail_accounting.data_entry_forms
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

                # Audit

                delete_form106_audit(
                    cur=cur,
                    tenant_id=request.tenant_id,
                    store=request.def_store,
                    date_value=request.def_date,
                    form_type=request.def_form_type,
                    user=request.def_user,
                    department_description=d_description,
                    amount=db_amount,
                    identity=request.def_id
                )

                conn.commit()

                return {
                    "return_value": 0,
                    "error_message": "",
                    "message": "Form106 deleted successfully."
                }

    except Exception as e:

        if conn:
            conn.rollback()

        logger.exception("Error in Form106 Delete")

        return {
            "return_value": 1,
            "error_message": f"Delete Failed: {str(e)}"
        }