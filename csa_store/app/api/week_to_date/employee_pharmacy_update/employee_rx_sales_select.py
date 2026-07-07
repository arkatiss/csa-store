import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.employee_pharmacy_update.employee_rx_sales_select_schema import EmployeeRXSalesSelectRequest, EmployeeRXSalesSelectResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/employee_pharmacy_update",
    tags=["Week To Date Employee Pharmacy Update"]
)

@router.post("/employee_rx_sales_select", response_model=EmployeeRXSalesSelectResponse)
def csa_employee_rx_sales_select(request: EmployeeRXSalesSelectRequest):
    """
    Equivalent of:
    csa_EmployeeRX_Sales_Select
    """
    try:
        if request.store is None:
            return EmployeeRXSalesSelectResponse(
                return_value=1,
                error_message="Invalid Store"
            )
            
        if request.week_ending_date is None:
            return EmployeeRXSalesSelectResponse(
                return_value=1,
                error_message="Invalid Week Ending Date"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if row for sales exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_dept_sales
                    WHERE wds_store = %s AND wds_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return EmployeeRXSalesSelectResponse(
                        return_value=3,
                        error_message="Row for sales not found"
                    )

                # Check if row for customer count exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_customer_count
                    WHERE wcc_store = %s AND wcc_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return EmployeeRXSalesSelectResponse(
                        return_value=4,
                        error_message="Row for customer count not found"
                    )

                # Retrieve amounts
                cur.execute("""
                    SELECT wds_pharmacy,
                           wcc_pharmacy,
                           wds_other,
                           wcc_other
                    FROM retail_accounting.wtd_dept_sales
                    INNER JOIN retail_accounting.wtd_customer_count
                        ON wds_store = wcc_store
                        AND wds_week_ending_date = wcc_week_ending_date
                    WHERE wds_store = %s AND wds_week_ending_date = %s
                """, (request.store, request.week_ending_date))
                
                row = cur.fetchone()
                if row:
                    return EmployeeRXSalesSelectResponse(
                        return_value=0,
                        error_message="",
                        wds_pharmacy=float(row[0]) if row[0] is not None else 0.0,
                        wcc_pharmacy=int(row[1]) if row[1] is not None else 0,
                        wds_employee_rx=float(row[2]) if row[2] is not None else 0.0,
                        wcc_employee_rx=int(row[3]) if row[3] is not None else 0
                    )
                else:
                    # Should not reach here based on earlier count checks, but just in case
                    return EmployeeRXSalesSelectResponse(
                        return_value=1,
                        error_message="Error retrieving amounts"
                    )

    except Exception as ex:
        logger.exception("Error in EmployeeRX_Sales_Select")
        return EmployeeRXSalesSelectResponse(
            return_value=1,
            error_message="Retrieve Employee RX Sales Failed"
        )
