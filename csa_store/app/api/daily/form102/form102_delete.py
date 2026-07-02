import logging
from fastapi import APIRouter
from datetime import timedelta
from app.core.db_utils import DBConnection
from app.schemas.daily.form102.form102_delete_schema import Form102DeleteRequest
from app.utils.daily.form102_helper import (
    get_week_ending_date,
    update_dsc_with_form102
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form102",
    tags=["Form102"]
)

@router.delete("/delete")
def csa_form102_delete(request: Form102DeleteRequest):
    """
    Equivalent of:
    csa_Form102_Delete
    """
    try:
        if request.def_id is None:
            return {"return_value": 1, "error_message": "Invalid Identity"}
        if request.def_store is None:
            return {"return_value": 1, "error_message": "Invalid Store"}

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch Store Configuration
                cur.execute("""
                    SELECT sc_eow_last_run, sc_eod_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """, (request.def_store,))
                
                config_row = cur.fetchone()
                if not config_row:
                    return {"return_value": 1, "error_message": "Store Configuration Not Found"}

                sc_eow_last_run = config_row[0].date() if config_row[0] else None
                sc_eod_last_run = config_row[1].date() if config_row[1] else None

                if not sc_eow_last_run or not sc_eod_last_run:
                    return {"return_value": 1, "error_message": "Invalid Store Configuration Dates"}

                # 2. Date Calculations and Validations
                week_ending_date = get_week_ending_date(sc_eow_last_run)

                # Custom date validation for delete
                start_date = week_ending_date - timedelta(days=7)
                end_date = week_ending_date + timedelta(days=1)
                
                if not (start_date <= request.def_date <= end_date):
                    return {"return_value": 1, "error_message": "Invalid Date"}

                # 3. Request Validations
                if request.def_form_type != 1:
                    return {"return_value": 1, "error_message": "Invalid Form Type"}
                if not request.def_user or request.def_user.strip() == "":
                    return {"return_value": 1, "error_message": "Invalid User"}

                # 4. Check Identity and old values
                cur.execute("""
                    SELECT def_store, def_date, def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id = %s AND def_id = %s
                """, (str(request.tenant_id), request.def_id))
                
                existing_record = cur.fetchone()
                if not existing_record:
                    return {"return_value": 1, "error_message": "Identity Not Found"}
                
                i_def_store = existing_record[0]
                i_def_date = existing_record[1].date() if existing_record[1] else None
                i_def_amount_2 = float(existing_record[2]) if existing_record[2] is not None else 0.0

                if i_def_store != request.def_store:
                    return {"return_value": 1, "error_message": "Wrong Store"}
                if i_def_date != request.def_date:
                    return {"return_value": 1, "error_message": "Wrong Date"}

                # 5. Delete Record
                cur.execute("""
                    DELETE FROM retail_accounting.data_entry_forms
                    WHERE def_id = %s
                """, (request.def_id,))

                # 6. Update DSCT
                update_dsc_with_form102(
                    cur, str(request.tenant_id), request.def_store, week_ending_date, sc_eod_last_run
                )

                # 7. Audit Logging
                audit_comment = f"Amount - {i_def_amount_2:.2f}, Identity - {request.def_id}"
                cur.execute("""
                    INSERT INTO retail_history.audit (
                        tenant_id, a_store, a_date, a_form_type, 
                        a_action, a_creation_date, a_user, a_comment
                    ) VALUES (
                        %s, %s, %s, %s, 'D', CURRENT_TIMESTAMP, %s, %s
                    )
                """, (
                    str(request.tenant_id), request.def_store, request.def_date, 
                    request.def_form_type, request.def_user, audit_comment
                ))

                return {
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:
        logger.exception("Error in Form102 Delete")
        return {
            "return_value": 1,
            "error_message": "Delete Failed" if "update_dsc" not in str(ex).lower() else "Update Failed"
        }
