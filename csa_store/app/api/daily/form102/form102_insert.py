import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily.form102.form102_insert_schema import Form102InsertRequest
from app.utils.daily.form102_helper import (
    get_week_ending_date,
    is_valid_date,
    is_store_open,
    update_dsc_with_form102
)
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form102",
    tags=["Form102"]
)

@router.post("/insert")
def csa_form102_insert(request: Form102InsertRequest):
    """
    Equivalent of:
    csa_Form102_Insert
    """
    try:
        # VALIDATE STORE
        if request.def_store is None:
            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch Store Configuration
                cur.execute("""
                    SELECT
                        sc_eow_last_run,
                        sc_eod_last_run,
                        sc_open_days
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """,
                            (
                                request.def_store,
                            ))

                config_row = cur.fetchone()
                if not config_row:
                    return {
                        "return_value": 1,
                        "error_message": "Store Configuration Not Found"
                    }

                sc_eow_last_run = config_row[0].date() if config_row[0] else None
                sc_eod_last_run = config_row[1].date() if config_row[1] else None
                sc_open_days = config_row[2]

                if not sc_eow_last_run or not sc_eod_last_run:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store Configuration Dates"
                    }

                # 2. Date Calculations and Validations
                week_ending_date = get_week_ending_date(sc_eow_last_run)

                if not is_valid_date(request.def_date, week_ending_date):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                if not is_store_open(sc_open_days, request.def_date):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date.  Store not open on this date."
                    }

                # 3. Request Validations
                if request.def_form_type != 1:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Form Type"
                    }
                
                if not request.def_user or request.def_user.strip() == "":
                    return {
                        "return_value": 1,
                        "error_message": "Invalid User"
                    }

                if not request.def_descriptor_1 or request.def_descriptor_1.strip() == "":
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Deposit Type"
                    }
                
                if request.def_amount_2 is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Deposit Amount"
                    }

                # 4. Insert into DataEntryForms
                # DBConnection provides transactional context. If exception is raised, it rolls back.
                cur.execute("""
                    INSERT INTO retail_accounting.data_entry_forms (
                        tenant_id, def_store, def_date, def_form_type, def_department,
                        def_user, def_descriptor_1, def_descriptor_2, def_descriptor_3,
                        def_descriptor_4, def_amount_1, def_amount_2, def_retail_acct_update_flag
                    ) VALUES (
                        %s, %s, %s, %s, NULL, 
                        %s, %s, %s, NULL, 
                        NULL, 0, %s, 'N'
                    ) RETURNING def_id
                """, (
                    str(request.tenant_id), request.def_store, request.def_date, request.def_form_type,
                    request.def_user, request.def_descriptor_1, request.def_descriptor_2, request.def_amount_2
                ))
                
                inserted_id = cur.fetchone()[0]

                # 5. Call Helper to Update DailySalesCashTotal with Deposits
                update_dsc_with_form102(
                    cur, 
                    str(request.tenant_id), 
                    request.def_store, 
                    week_ending_date, 
                    sc_eod_last_run
                )

                # 6. Audit Trail
                audit_comment = f"Amount - {request.def_amount_2:.2f}, Identity - {inserted_id}"
                cur.execute("""
                    INSERT INTO retail_history.audit (
                        tenant_id, a_store, a_date, a_form_type, 
                        a_action, a_creation_date, a_user, a_comment
                    ) VALUES (
                        %s, %s, %s, %s, 
                        'I', CURRENT_TIMESTAMP, %s, %s
                    )
                """, (
                    str(request.tenant_id), request.def_store, request.def_date, request.def_form_type,
                    request.def_user, audit_comment
                ))

                return {
                    "return_value": 0,
                    "error_message": "",
                    "id": inserted_id
                }

    except Exception as ex:
        logger.exception("Error in Form102 Insert")
        return {
            "return_value": 1,
            "error_message": "Insert Failed" if "update_dsc" not in str(ex).lower() else "Update Failed"
            # We simplify error message as exception details are logged.
        }
