import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily_department_input_ind_only.dept_customer_count_manual_update_schema import DeptCustomerCountManualUpdateRequest
from app.utils.form102_helper import get_week_ending_date

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily_department_input_ind_only/customer_count_manual",
    tags=["Daily Department Input Ind Only"]
)

@router.put("/update")
def csa_daily_customer_count_manual_update(request: DeptCustomerCountManualUpdateRequest):
    """
    Equivalent of:
    csa_DailyCustomerCount_Manual_Update
    """
    try:
        if request.dccm_store is None:
            return {"return_value": 1, "error_message": "Invalid Store"}
        if request.dccm_file_date is None:
            return {"return_value": 1, "error_message": "Invalid Date"}
        if not request.user or request.user.strip() == "":
            return {"return_value": 1, "error_message": "Invalid User"}
        
        if request.dccm_restaurant is None:
            return {"return_value": 1, "error_message": "Invalid Restaurant"}
        if request.dccm_fuelgrocery is None:
            return {"return_value": 1, "error_message": "Invalid FuelGrocery"}
        if request.dccm_other3 is None:
            return {"return_value": 1, "error_message": "Invalid Other3"}
        if request.dccm_other4 is None:
            return {"return_value": 1, "error_message": "Invalid Other4"}
        if request.dccm_other5 is None:
            return {"return_value": 1, "error_message": "Invalid Other5"}

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch Store Configuration
                cur.execute("""
                    SELECT sc_eow_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """, (request.dccm_store,))
                
                config_row = cur.fetchone()
                sc_eow_last_run = config_row[0].date() if config_row and config_row[0] else None
                
                # We do need a valid EOW date to calculate week ending date
                if not sc_eow_last_run:
                    return {"return_value": 1, "error_message": "Store Configuration Not Found"}

                # Use our helper for WeekEndingDate
                week_ending_date = get_week_ending_date(sc_eow_last_run)

                # 2. Check if row exists and gets old values
                cur.execute("""
                    SELECT count(*)
                    FROM retail.daily_customer_count_manual
                    WHERE dccm_store = %s AND dccm_file_date = %s
                """, (request.dccm_store, request.dccm_file_date))
                count_record = cur.fetchone()
                
                if not count_record or count_record[0] == 0:
                    return {"return_value": 1, "error_message": "Row Not Found"}

                cur.execute("""
                    SELECT dccm_restaurant, dccm_fuelgrocery, dccm_other3, dccm_other4, dccm_other5
                    FROM retail.daily_customer_count_manual
                    WHERE dccm_store = %s AND dccm_file_date = %s
                """, (request.dccm_store, request.dccm_file_date))
                
                old_record = cur.fetchone()
                
                old_restaurant = int(old_record[0]) if old_record[0] is not None else 0
                old_fuelgrocery = int(old_record[1]) if old_record[1] is not None else 0
                old_other3 = int(old_record[2]) if old_record[2] is not None else 0
                old_other4 = int(old_record[3]) if old_record[3] is not None else 0
                old_other5 = int(old_record[4]) if old_record[4] is not None else 0

                # 3. Check for No Updates Detected
                if (old_restaurant == request.dccm_restaurant and 
                    old_fuelgrocery == request.dccm_fuelgrocery and 
                    old_other3 == request.dccm_other3 and 
                    old_other4 == request.dccm_other4 and 
                    old_other5 == request.dccm_other5):
                    return {"return_value": 1, "error_message": "No Updates Detected"}

                # 4. Update Daily Customer Count Manual
                cur.execute("""
                    UPDATE retail.daily_customer_count_manual
                    SET dccm_restaurant = %s,
                        dccm_fuelgrocery = %s,
                        dccm_other3 = %s,
                        dccm_other4 = %s,
                        dccm_other5 = %s,
                        last_updated_by = %s,
                        last_update_date = CURRENT_TIMESTAMP
                    WHERE dccm_store = %s AND dccm_file_date = %s
                """, (
                    request.dccm_restaurant, request.dccm_fuelgrocery, request.dccm_other3, 
                    request.dccm_other4, request.dccm_other5, request.user,
                    request.dccm_store, request.dccm_file_date
                ))

                # 5. Update WTD Customer Count Manual using CTE
                cur.execute("""
                    WITH query1 AS (
                        SELECT 
                            dccm_store,
                            sum(dccm_restaurant) as restaurant,
                            sum(dccm_fuelgrocery) as fuelgrocery,
                            sum(dccm_other3) as other3,
                            sum(dccm_other4) as other4,
                            sum(dccm_other5) as other5
                        FROM retail.daily_customer_count_manual
                        WHERE dccm_store = %s
                        GROUP BY dccm_store
                    )
                    UPDATE retail.wtd_customer_count_manual
                    SET wccm_restaurant = query1.restaurant,
                        wccm_fuel_grocery = query1.fuelgrocery,
                        wccm_other3 = query1.other3,
                        wccm_other4 = query1.other4,
                        wccm_other5 = query1.other5,
                        last_updated_by = %s,
                        last_update_date = CURRENT_TIMESTAMP
                    FROM query1
                    WHERE wccm_store = query1.dccm_store
                      AND wccm_store = %s
                      AND wccm_week_ending_date = %s
                """, (
                    request.dccm_store, 
                    request.user, 
                    request.dccm_store, 
                    week_ending_date
                ))

                # 6. Audit Logging
                audit_logs = []
                
                if old_restaurant != request.dccm_restaurant:
                    comment = f"Restaurant Customer Count  Changed From - {old_restaurant} To - {request.dccm_restaurant}"
                    audit_logs.append(comment)
                    
                if old_fuelgrocery != request.dccm_fuelgrocery:
                    comment = f"FuelGrocery Customer Count  Changed From - {old_fuelgrocery} To - {request.dccm_fuelgrocery}"
                    audit_logs.append(comment)
                    
                if old_other3 != request.dccm_other3:
                    comment = f"Other 3 Customer Count  Changed From - {old_other3} To - {request.dccm_other3}"
                    audit_logs.append(comment)
                    
                if old_other4 != request.dccm_other4:
                    comment = f"Other 4 Customer Count  Changed From - {old_other4} To - {request.dccm_other4}"
                    audit_logs.append(comment)
                    
                if old_other5 != request.dccm_other5:
                    comment = f"Other 5 Customer Count  Changed From - {old_other5} To - {request.dccm_other5}"
                    audit_logs.append(comment)

                for comment in audit_logs:
                    cur.execute("""
                        INSERT INTO retail_history.audit (
                            tenant_id, a_store, a_date, a_form_type, 
                            a_action, a_creation_date, a_user, a_comment
                        ) VALUES (
                            %s, %s, %s, 16, 'U', CURRENT_TIMESTAMP, %s, %s
                        )
                    """, (
                        str(request.tenant_id), request.dccm_store, request.dccm_file_date, 
                        request.user, comment
                    ))

                return {
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:
        logger.exception("Error in DailyCustomerCount_Manual Update")
        return {
            "return_value": 1,
            "error_message": "Update DailyCustomerCount_Manual Failed"
        }
