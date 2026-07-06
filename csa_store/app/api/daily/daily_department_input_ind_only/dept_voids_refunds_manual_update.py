import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily.daily_department_input_ind_only.dept_voids_refunds_manual_update_schema import DeptVoidsRefundsManualUpdateRequest
from app.utils.daily.form102_helper import get_week_ending_date

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/daily_department_input_ind_only/voids_refunds_manual",
    tags=["Daily Department Input Ind Only"]
)

@router.put("/update")
def csa_daily_dept_voids_refunds_manual_update(request: DeptVoidsRefundsManualUpdateRequest):
    """
    Equivalent of:
    csa_DailyDeptVoidsRefunds_Manual_Update
    """
    try:
        if request.ddvrm_store is None:
            return {"return_value": 1, "error_message": "Invalid Store"}
        if request.ddvrm_file_date is None:
            return {"return_value": 1, "error_message": "Invalid Date"}
        if not request.user or request.user.strip() == "":
            return {"return_value": 1, "error_message": "Invalid User"}
        
        if request.ddvrm_restaurant is None:
            return {"return_value": 1, "error_message": "Invalid Restaurant"}
        if request.ddvrm_fuelgrocery is None:
            return {"return_value": 1, "error_message": "Invalid FuelGrocery"}
        if request.ddvrm_other3 is None:
            return {"return_value": 1, "error_message": "Invalid Other3"}
        if request.ddvrm_other4 is None:
            return {"return_value": 1, "error_message": "Invalid Other4"}
        if request.ddvrm_other5 is None:
            return {"return_value": 1, "error_message": "Invalid Other5"}

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch Store Configuration
                cur.execute("""
                    SELECT sc_eow_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """, (request.ddvrm_store,))
                
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
                    FROM retail.daily_dept_voids_refunds_manual
                    WHERE ddvrm_store = %s AND ddvrm_file_date = %s
                """, (request.ddvrm_store, request.ddvrm_file_date))
                count_record = cur.fetchone()
                
                if not count_record or count_record[0] == 0:
                    return {"return_value": 1, "error_message": "Row Not Found"}

                cur.execute("""
                    SELECT ddvrm_restaurant, ddvrm_fuelgrocery, ddvrm_other3, ddvrm_other4, ddvrm_other5
                    FROM retail.daily_dept_voids_refunds_manual
                    WHERE ddvrm_store = %s AND ddvrm_file_date = %s
                """, (request.ddvrm_store, request.ddvrm_file_date))
                
                old_record = cur.fetchone()
                
                old_restaurant = float(old_record[0]) if old_record[0] is not None else 0.0
                old_fuelgrocery = float(old_record[1]) if old_record[1] is not None else 0.0
                old_other3 = float(old_record[2]) if old_record[2] is not None else 0.0
                old_other4 = float(old_record[3]) if old_record[3] is not None else 0.0
                old_other5 = float(old_record[4]) if old_record[4] is not None else 0.0

                # 3. Check for No Updates Detected
                if (old_restaurant == request.ddvrm_restaurant and 
                    old_fuelgrocery == request.ddvrm_fuelgrocery and 
                    old_other3 == request.ddvrm_other3 and 
                    old_other4 == request.ddvrm_other4 and 
                    old_other5 == request.ddvrm_other5):
                    return {"return_value": 1, "error_message": "No Updates Detected"}

                # 4. Update Daily Dept Voids Refunds Manual
                cur.execute("""
                    UPDATE retail.daily_dept_voids_refunds_manual
                    SET ddvrm_restaurant = %s,
                        ddvrm_fuelgrocery = %s,
                        ddvrm_other3 = %s,
                        ddvrm_other4 = %s,
                        ddvrm_other5 = %s,
                        last_updated_by = %s,
                        last_update_date = CURRENT_TIMESTAMP
                    WHERE ddvrm_store = %s AND ddvrm_file_date = %s
                """, (
                    request.ddvrm_restaurant, request.ddvrm_fuelgrocery, request.ddvrm_other3, 
                    request.ddvrm_other4, request.ddvrm_other5, request.user,
                    request.ddvrm_store, request.ddvrm_file_date
                ))

                # 5. Update WTD Dept Voids Refunds Manual using CTE
                cur.execute("""
                    WITH query1 AS (
                        SELECT 
                            ddvrm_store,
                            sum(ddvrm_restaurant) as restaurant,
                            sum(ddvrm_fuelgrocery) as fuelgrocery,
                            sum(ddvrm_other3) as other3,
                            sum(ddvrm_other4) as other4,
                            sum(ddvrm_other5) as other5
                        FROM retail.daily_dept_voids_refunds_manual
                        WHERE ddvrm_store = %s
                        GROUP BY ddvrm_store
                    )
                    UPDATE retail.wtd_dept_voids_refunds_manual
                    SET wdvrm_restaurant = query1.restaurant,
                        wdvrm_fuel_grocery = query1.fuelgrocery,
                        wdvrm_other3 = query1.other3,
                        wdvrm_other4 = query1.other4,
                        wdvrm_other5 = query1.other5,
                        last_updated_by = %s,
                        last_update_date = CURRENT_TIMESTAMP
                    FROM query1
                    WHERE wdvrm_store = query1.ddvrm_store
                      AND wdvrm_store = %s
                      AND wdvrm_week_ending_date = %s
                """, (
                    request.ddvrm_store, 
                    request.user, 
                    request.ddvrm_store, 
                    week_ending_date
                ))

                # 6. Audit Logging
                audit_logs = []
                
                if old_restaurant != request.ddvrm_restaurant:
                    comment = f"Restaurant Daily Voids and Refunds Changed From - {old_restaurant:.2f} To - {request.ddvrm_restaurant:.2f}"
                    audit_logs.append(comment)
                    
                if old_fuelgrocery != request.ddvrm_fuelgrocery:
                    comment = f"FuelGrocery Daily Voids and Refunds Changed From - {old_fuelgrocery:.2f} To - {request.ddvrm_fuelgrocery:.2f}"
                    audit_logs.append(comment)
                    
                if old_other3 != request.ddvrm_other3:
                    comment = f"Other 3 Daily Voids and Refunds Changed From - {old_other3:.2f} To - {request.ddvrm_other3:.2f}"
                    audit_logs.append(comment)
                    
                if old_other4 != request.ddvrm_other4:
                    comment = f"Other 4 Daily Voids and Refunds Changed From - {old_other4:.2f} To - {request.ddvrm_other4:.2f}"
                    audit_logs.append(comment)
                    
                if old_other5 != request.ddvrm_other5:
                    comment = f"Other 5 Daily Voids and Refunds Changed From - {old_other5:.2f} To - {request.ddvrm_other5:.2f}"
                    audit_logs.append(comment)

                for comment in audit_logs:
                    cur.execute("""
                        INSERT INTO retail_history.audit (
                            tenant_id, a_store, a_date, a_form_type, 
                            a_action, a_creation_date, a_user, a_comment
                        ) VALUES (
                            %s, %s, %s, 17, 'U', CURRENT_TIMESTAMP, %s, %s
                        )
                    """, (
                        str(request.tenant_id), request.ddvrm_store, request.ddvrm_file_date, 
                        request.user, comment
                    ))

                return {
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:
        logger.exception("Error in DailyDeptVoidsRefunds_Manual Update")
        return {
            "return_value": 1,
            "error_message": "Update Daily Voids Refunds (Manual) Failed"
        }
