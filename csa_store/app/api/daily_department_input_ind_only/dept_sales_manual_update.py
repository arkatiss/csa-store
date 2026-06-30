import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily_department_input_ind_only.dept_sales_manual_update_schema import DeptSalesManualUpdateRequest
from app.utils.form102_helper import get_week_ending_date

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily_department_input_ind_only/sales_manual",
    tags=["Daily Department Input Ind Only"]
)

@router.put("/update")
def csa_daily_dept_sales_manual_update(request: DeptSalesManualUpdateRequest):
    """
    Equivalent of:
    csa_DailyDeptSales_Manual_Update
    """
    try:
        if request.ddsm_store is None:
            return {"return_value": 1, "error_message": "Invalid Store"}
        if request.ddsm_file_date is None:
            return {"return_value": 1, "error_message": "Invalid Date"}
        if not request.user or request.user.strip() == "":
            return {"return_value": 1, "error_message": "Invalid User"}
        
        if request.ddsm_restaurant is None:
            return {"return_value": 1, "error_message": "Invalid Restaurant"}
        if request.ddsm_fuelgrocery is None:
            return {"return_value": 1, "error_message": "Invalid FuelGrocery"}
        if request.ddsm_other3 is None:
            return {"return_value": 1, "error_message": "Invalid Other3"}
        if request.ddsm_other4 is None:
            return {"return_value": 1, "error_message": "Invalid Other4"}
        if request.ddsm_other5 is None:
            return {"return_value": 1, "error_message": "Invalid Other5"}

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch Store Configuration
                cur.execute("""
                    SELECT sc_eow_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """, (request.ddsm_store,))
                
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
                    FROM retail.daily_dept_sales_manual
                    WHERE ddsm_store = %s AND ddsm_file_date = %s AND ddsm_process_flag = '0'
                """, (request.ddsm_store, request.ddsm_file_date))
                count_record = cur.fetchone()
                
                if not count_record or count_record[0] == 0:
                    return {"return_value": 1, "error_message": "Row Not Found"}

                cur.execute("""
                    SELECT ddsm_restaurant, ddsm_fuelgrocery, ddsm_other3, ddsm_other4, ddsm_other5
                    FROM retail.daily_dept_sales_manual
                    WHERE ddsm_store = %s AND ddsm_file_date = %s
                """, (request.ddsm_store, request.ddsm_file_date))
                
                old_record = cur.fetchone()
                
                old_restaurant = float(old_record[0]) if old_record[0] is not None else 0.0
                old_fuelgrocery = float(old_record[1]) if old_record[1] is not None else 0.0
                old_other3 = float(old_record[2]) if old_record[2] is not None else 0.0
                old_other4 = float(old_record[3]) if old_record[3] is not None else 0.0
                old_other5 = float(old_record[4]) if old_record[4] is not None else 0.0

                # 3. Check for No Updates Detected
                if (old_restaurant == request.ddsm_restaurant and 
                    old_fuelgrocery == request.ddsm_fuelgrocery and 
                    old_other3 == request.ddsm_other3 and 
                    old_other4 == request.ddsm_other4 and 
                    old_other5 == request.ddsm_other5):
                    return {"return_value": 1, "error_message": "No Updates Detected"}

                # 4. Update Daily Dept Sales Manual
                cur.execute("""
                    UPDATE retail.daily_dept_sales_manual
                    SET ddsm_restaurant = %s,
                        ddsm_fuelgrocery = %s,
                        ddsm_other3 = %s,
                        ddsm_other4 = %s,
                        ddsm_other5 = %s,
                        last_updated_by = %s,
                        last_update_date = CURRENT_TIMESTAMP
                    WHERE ddsm_store = %s AND ddsm_file_date = %s
                """, (
                    request.ddsm_restaurant, request.ddsm_fuelgrocery, request.ddsm_other3, 
                    request.ddsm_other4, request.ddsm_other5, request.user,
                    request.ddsm_store, request.ddsm_file_date
                ))

                # 5. Update WTD Dept Sales Manual using CTE
                cur.execute("""
                    WITH query1 AS (
                        SELECT 
                            ddsm_store,
                            sum(ddsm_restaurant) as restaurant,
                            sum(ddsm_fuelgrocery) as fuelgrocery,
                            sum(ddsm_other3) as other3,
                            sum(ddsm_other4) as other4,
                            sum(ddsm_other5) as other5
                        FROM retail.daily_dept_sales_manual
                        WHERE ddsm_store = %s
                        GROUP BY ddsm_store
                    )
                    UPDATE retail.wtd_dept_sales_manual
                    SET wdsm_restaurant = query1.restaurant,
                        wdsm_fuel_grocery = query1.fuelgrocery,
                        wdsm_other3 = query1.other3,
                        wdsm_other4 = query1.other4,
                        wdsm_other5 = query1.other5,
                        last_updated_by = %s,
                        last_update_date = CURRENT_TIMESTAMP
                    FROM query1
                    WHERE wdsm_store = query1.ddsm_store
                      AND wdsm_store = %s
                      AND wdsm_week_ending_date = %s
                """, (
                    request.ddsm_store, 
                    request.user, 
                    request.ddsm_store, 
                    week_ending_date
                ))

                # 6. Audit Logging
                audit_logs = []
                
                if old_restaurant != request.ddsm_restaurant:
                    comment = f"Restaurant Daily Sales Changed From - {old_restaurant:.2f} To - {request.ddsm_restaurant:.2f}"
                    audit_logs.append(comment)
                    
                if old_fuelgrocery != request.ddsm_fuelgrocery:
                    comment = f"FuelGrocery Daily Sales Changed From - {old_fuelgrocery:.2f} To - {request.ddsm_fuelgrocery:.2f}"
                    audit_logs.append(comment)
                    
                if old_other3 != request.ddsm_other3:
                    comment = f"Other 3 Daily Sales Changed From - {old_other3:.2f} To - {request.ddsm_other3:.2f}"
                    audit_logs.append(comment)
                    
                if old_other4 != request.ddsm_other4:
                    comment = f"Other 4 Daily Sales Changed From - {old_other4:.2f} To - {request.ddsm_other4:.2f}"
                    audit_logs.append(comment)
                    
                if old_other5 != request.ddsm_other5:
                    comment = f"Other 5 Daily Sales Changed From - {old_other5:.2f} To - {request.ddsm_other5:.2f}"
                    audit_logs.append(comment)

                for comment in audit_logs:
                    cur.execute("""
                        INSERT INTO retail_history.audit (
                            tenant_id, a_store, a_date, a_form_type, 
                            a_action, a_creation_date, a_user, a_comment
                        ) VALUES (
                            %s, %s, %s, 18, 'U', CURRENT_TIMESTAMP, %s, %s
                        )
                    """, (
                        str(request.tenant_id), request.ddsm_store, request.ddsm_file_date, 
                        request.user, comment
                    ))

                return {
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:
        logger.exception("Error in DailyDeptSales_Manual Update")
        return {
            "return_value": 1,
            "error_message": "Update Daily Dept Sales (Manual) Failed"
        }
