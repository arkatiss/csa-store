import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily.form102.form102_update_schema import Form102UpdateRequest
from app.utils.daily.form102_helper import (
    get_week_ending_date,
    is_valid_date,
    is_store_open,
    update_dsc_with_form102
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form102",
    tags=["Form102"]
)

@router.put("/update")
def csa_form102_update(request: Form102UpdateRequest):
    """
    Equivalent of:
    csa_Form102_Update
    """
    try:
        if request.def_id is None:
            return {"return_value": 1, "error_message": "Invalid ID"}
        if request.def_store is None:
            return {"return_value": 1, "error_message": "Invalid Store"}

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch Store Configuration
                cur.execute("""
                    SELECT sc_eow_last_run, sc_eod_last_run, sc_open_days
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """, (request.def_store,))
                
                config_row = cur.fetchone()
                if not config_row:
                    return {"return_value": 1, "error_message": "Store Configuration Not Found"}

                sc_eow_last_run = config_row[0].date() if config_row[0] else None
                sc_eod_last_run = config_row[1].date() if config_row[1] else None
                sc_open_days = config_row[2]

                if not sc_eow_last_run or not sc_eod_last_run:
                    return {"return_value": 1, "error_message": "Invalid Store Configuration Dates"}

                # 2. Date Calculations and Validations
                week_ending_date = get_week_ending_date(sc_eow_last_run)

                if not is_valid_date(request.def_date, week_ending_date):
                    return {"return_value": 1, "error_message": "Invalid Date"}

                if not is_store_open(sc_open_days, request.def_date):
                    return {"return_value": 1, "error_message": "Invalid Date.  Store not open on this date."}

                # 3. Request Validations
                if request.def_form_type != 1:
                    return {"return_value": 1, "error_message": "Invalid Form Type"}
                if not request.def_user or request.def_user.strip() == "":
                    return {"return_value": 1, "error_message": "Invalid User"}
                if not request.def_descriptor_1 or request.def_descriptor_1.strip() == "":
                    return {"return_value": 1, "error_message": "Invalid Deposit Type"}
                if request.def_amount_2 is None:
                    return {"return_value": 1, "error_message": "Invalid Deposit Amount"}

                # 4. Check Identity and old values
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id = %s
                """, (request.def_id,))
                
                count_record = cur.fetchone()
                if not count_record:
                    return {"return_value": 1, "error_message": "Identity Not Found"}

                cur.execute("""
                                    SELECT def_store, def_date, def_form_type, def_user, 
                           def_descriptor_1, def_descriptor_2, def_amount_2
                                    FROM retail_accounting.data_entry_forms
                                    WHERE def_id = %s
                                """, (request.def_id,))

                old_record = cur.fetchone()
                
                old_store = old_record[0]
                old_date = old_record[1].date() if old_record[1] else None
                old_form_type = old_record[2]
                old_user = old_record[3]
                old_desc_1 = old_record[4]
                old_desc_2 = old_record[5]
                old_amount_2 = float(old_record[6]) if old_record[6] is not None else 0.0

                if old_store != request.def_store:
                    return {"return_value": 1, "error_message": "Invalid Store"}
                if old_form_type != request.def_form_type:
                    return {"return_value": 1, "error_message": "Invalid Form Type"}

                # 5. Update Record
                cur.execute("""
                    UPDATE retail_accounting.data_entry_forms
                    SET def_date = %s,
                        def_user = %s,
                        def_descriptor_1 = %s,
                        def_descriptor_2 = %s,
                        def_amount_2 = %s
                    WHERE def_id = %s
                """, (
                    request.def_date, request.def_user, request.def_descriptor_1, 
                    request.def_descriptor_2, request.def_amount_2, request.def_id
                ))

                # 6. Update DSCT
                update_dsc_with_form102(
                    cur, str(request.tenant_id), request.def_store, week_ending_date, sc_eod_last_run
                )

                # 7. Audit Logging for changes
                def insert_audit(comment):
                    cur.execute("""
                        INSERT INTO retail_history.audit (
                            tenant_id, a_store, a_date, a_form_type, 
                            a_action, a_creation_date, a_user, a_comment
                        ) VALUES (
                            %s, %s, %s, %s, 'U', CURRENT_TIMESTAMP, %s, %s
                        )
                    """, (str(request.tenant_id), request.def_store, request.def_date, 
                          request.def_form_type, request.def_user, comment))

                if old_date != request.def_date:
                    insert_audit(f"Date Changed From: {old_date.strftime('%m/%d/%y')} To: {request.def_date.strftime('%m/%d/%y')}")
                if old_user != request.def_user:
                    insert_audit(f"User Changed From: {old_user} To: {request.def_user}")
                if old_desc_1 != request.def_descriptor_1:
                    insert_audit(f"Descriptor 1 Changed From: {old_desc_1} To: {request.def_descriptor_1}")
                if old_desc_2 != request.def_descriptor_2:
                    insert_audit(f"Descriptor 2 Changed From: {old_desc_2 or ''} To: {request.def_descriptor_2 or ''}")
                if old_amount_2 != request.def_amount_2:
                    insert_audit(f"Amount 2 Changed From: {old_amount_2:.2f} To: {request.def_amount_2:.2f}")

                return {
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:
        logger.exception("Error in Form102 Update")
        return {
            "return_value": 1,
            "error_message": "Update Failed"
        }
