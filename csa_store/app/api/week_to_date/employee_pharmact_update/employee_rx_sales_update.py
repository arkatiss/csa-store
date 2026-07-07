import logging
from datetime import datetime
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.employee_pharmact_update.employee_rx_sales_update_schema import EmployeeRXSalesUpdateRequest, EmployeeRXSalesUpdateResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/employee_pharmact_update",
    tags=["Week To Date Employee Pharmacy Update"]
)

@router.put("/employee_rx_sales_update", response_model=EmployeeRXSalesUpdateResponse)
def csa_employee_rx_sales_update(request: EmployeeRXSalesUpdateRequest):
    """
    Equivalent of:
    csa_EmployeeRX_Sales_Update
    """
    try:
        if request.store is None:
            return EmployeeRXSalesUpdateResponse(return_value=1, error_message="Invalid Store")
            
        if request.week_ending_date is None:
            return EmployeeRXSalesUpdateResponse(return_value=1, error_message="Invalid Week Ending Date")

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Make sure Point-Of-Sale data is in for current sales date
                cur.execute("""
                    SELECT sc_eod_last_run 
                    FROM retail_accounting.store_configuration 
                    WHERE sc_store = %s
                """, (request.store,))
                
                sc_row = cur.fetchone()
                if not sc_row or sc_row[0] is None:
                    sales_date = None
                else:
                    # In Python, datetime from DB might already be datetime.date or datetime.datetime
                    # We cast it similarly to how SQL Server did it.
                    sales_date = sc_row[0].date() if isinstance(sc_row[0], datetime) else sc_row[0]
                
                if sales_date:
                    cur.execute("""
                        SELECT count(*)
                        FROM retail_history.pos
                        WHERE pos_store = %s AND pos_file_date = %s
                    """, (request.store, sales_date))
                    pos_count_record = cur.fetchone()
                    if not pos_count_record or pos_count_record[0] == 0:
                        return EmployeeRXSalesUpdateResponse(
                            return_value=1, 
                            error_message="You must have received your Point-of-sale figures before running this option"
                        )
                else:
                    return EmployeeRXSalesUpdateResponse(
                        return_value=1, 
                        error_message="You must have received your Point-of-sale figures before running this option"
                    )

                # 2. Make sure we are in a week-ending time frame
                current_date = datetime.now().date()
                day_of_week = current_date.strftime("%A")
                
                if day_of_week == "Monday" and (sales_date and sales_date < current_date):
                    pass # OK to run
                else:
                    return EmployeeRXSalesUpdateResponse(
                        return_value=1, 
                        error_message="You can only run this option at the end of the week"
                    )

                # Continue Validations
                if request.weekly_sales is None:
                    return EmployeeRXSalesUpdateResponse(return_value=1, error_message="Invalid Weekly Sales amount")
                    
                if request.weekly_customer_count is None:
                    return EmployeeRXSalesUpdateResponse(return_value=1, error_message="Invalid Weekly Customer Count amount")
                    
                if not request.user or str(request.user).strip() == '':
                    return EmployeeRXSalesUpdateResponse(return_value=1, error_message="Invalid User")

                # 3. Check for existence in sales and customer count tables
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_dept_sales
                    WHERE wds_store = %s AND wds_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                if cur.fetchone()[0] == 0:
                    return EmployeeRXSalesUpdateResponse(return_value=3, error_message="Row for sales not found")

                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_customer_count
                    WHERE wcc_store = %s AND wcc_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                if cur.fetchone()[0] == 0:
                    return EmployeeRXSalesUpdateResponse(return_value=4, error_message="Row for customer count not found")

                # 4. Fetch old values
                cur.execute("""
                    SELECT wds_other
                    FROM retail_accounting.wtd_dept_sales
                    WHERE wds_store = %s AND wds_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                old_wds_row = cur.fetchone()
                old_weekly_sales = float(old_wds_row[0]) if old_wds_row and old_wds_row[0] is not None else 0.0

                cur.execute("""
                    SELECT wcc_other
                    FROM retail_accounting.wtd_customer_count
                    WHERE wcc_store = %s AND wcc_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                old_wcc_row = cur.fetchone()
                old_weekly_customer_count = int(old_wcc_row[0]) if old_wcc_row and old_wcc_row[0] is not None else 0

                if old_weekly_sales == request.weekly_sales and old_weekly_customer_count == request.weekly_customer_count:
                    return EmployeeRXSalesUpdateResponse(return_value=5, error_message="No updates detected")

                # 5. Fetch total pharmacy values for limit checks
                cur.execute("""
                    SELECT wds_pharmacy + wds_other
                    FROM retail_accounting.wtd_dept_sales
                    WHERE wds_store = %s AND wds_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                tot_pharm_row = cur.fetchone()
                total_pharmacy_sales = float(tot_pharm_row[0]) if tot_pharm_row and tot_pharm_row[0] is not None else 0.0

                cur.execute("""
                    SELECT wcc_pharmacy + wcc_other
                    FROM retail_accounting.wtd_customer_count
                    WHERE wcc_store = %s AND wcc_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                tot_pharm_cc_row = cur.fetchone()
                total_pharmacy_customer_count = int(tot_pharm_cc_row[0]) if tot_pharm_cc_row and tot_pharm_cc_row[0] is not None else 0

                # 6. Prevent keying an amount greater than the total pharmacy
                if request.weekly_sales > total_pharmacy_sales:
                    return EmployeeRXSalesUpdateResponse(
                        return_value=6, 
                        error_message="You cannot key an amount greater than your total pharmacy sales"
                    )

                if request.weekly_customer_count > total_pharmacy_customer_count:
                    return EmployeeRXSalesUpdateResponse(
                        return_value=7, 
                        error_message="You cannot key an amount greater than your total pharmacy customer count"
                    )

                try:
                    # 7. Update Sales and Customer Count
                    cur.execute("""
                        UPDATE retail_accounting.wtd_dept_sales
                        SET wds_other = %s,
                            wds_pharmacy = %s
                        WHERE wds_store = %s AND wds_week_ending_date = %s
                    """, (request.weekly_sales, total_pharmacy_sales - request.weekly_sales, request.store, request.week_ending_date))

                    cur.execute("""
                        UPDATE retail_accounting.wtd_customer_count
                        SET wcc_other = %s,
                            wcc_pharmacy = %s
                        WHERE wcc_store = %s AND wcc_week_ending_date = %s
                    """, (request.weekly_customer_count, total_pharmacy_customer_count - request.weekly_customer_count, request.store, request.week_ending_date))

                    # (Optional/Commented out in original): csa_EmployeeRX_Sales_Prorate call would go here
                    
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    logger.exception("Update to Employee RX tables failed")
                    return EmployeeRXSalesUpdateResponse(return_value=8, error_message="Update Failed")

                # 8. Audit Logs
                audit_records = []
                if old_weekly_sales != request.weekly_sales:
                    audit_records.append((
                        request.tenant_id, request.store, request.week_ending_date, 45, 'U', request.user,
                        f"Employee RX Sales Changed From: {old_weekly_sales} To: {request.weekly_sales}"
                    ))
                
                if old_weekly_customer_count != request.weekly_customer_count:
                    audit_records.append((
                        request.tenant_id, request.store, request.week_ending_date, 45, 'U', request.user,
                        f"Employee RX Customer Count Changed From: {old_weekly_customer_count} To: {request.weekly_customer_count}"
                    ))

                if audit_records:
                    cur.executemany("""
                        INSERT INTO retail_history.audit
                        (tenant_id, a_store, a_date, a_form_type, a_action, a_creation_date, a_user, a_comment)
                        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
                    """, audit_records)
                    conn.commit()

                return EmployeeRXSalesUpdateResponse(return_value=0, error_message="")

    except Exception as ex:
        logger.exception("Error in EmployeeRX_Sales_Update")
        return EmployeeRXSalesUpdateResponse(
            return_value=1,
            error_message="Update Failed"
        )
