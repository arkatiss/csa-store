import logging
from fastapi import APIRouter, Query
from datetime import date
from uuid import UUID
from app.core.db_utils import DBConnection
from app.schemas.daily.daily_department_input_ind_only.dept_input_select_schema import (
    DeptInputSelectRequest, 
    DeptInputSelectResponse, 
    DeptInputRow
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/daily_department_input_ind_only",
    tags=["Daily Department Input Ind Only"]
)

@router.post("/select", response_model=DeptInputSelectResponse)
def csa_dept_input_select(request: DeptInputSelectRequest):
    """
    Equivalent of:
    csa_DeptInput_Select
    """
    try:
        if request.ddsm_store is None:
            return DeptInputSelectResponse(return_value=1, error_message="Invalid Store")
        if request.ddsm_file_date is None:
            return DeptInputSelectResponse(return_value=1, error_message="Invalid Date")

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch Store Configuration
                cur.execute("""
                    SELECT sc_eod_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """, (request.ddsm_store,))
                
                config_row = cur.fetchone()
                
                sc_eod_last_run = config_row[0].date() if config_row and config_row[0] else None
                
                if sc_eod_last_run != request.ddsm_file_date:
                    return DeptInputSelectResponse(return_value=1, error_message="Invalid Date")

                # 2. Query Data (UNION ALL equivalent)
                cur.execute("""
                    SELECT  'Sales' as row_description,
                            ddsm_restaurant as restaurant,
                            ddsm_fuelgrocery as fuelgrocery,
                            ddsm_other3 as other3,
                            ddsm_other4 as other4,
                            ddsm_other5 as other5
                    FROM    retail.daily_dept_sales_manual
                    WHERE   ddsm_store = %s AND
                            ddsm_file_date = %s
                    
                    UNION ALL
                    
                    SELECT  'Voids & Refunds' as row_description,
                            ddvrm_restaurant as restaurant,
                            ddvrm_fuelgrocery as fuelgrocery,
                            ddvrm_other3 as other3,
                            ddvrm_other4 as other4,
                            ddvrm_other5 as other5
                    FROM    retail.daily_dept_voids_refunds_manual
                    WHERE   ddvrm_store = %s AND
                            ddvrm_file_date = %s
                            
                    UNION ALL
                    
                    SELECT  'Customer Count' as row_description,
                            dccm_restaurant as restaurant,
                            dccm_fuelgrocery as fuelgrocery,
                            dccm_other3 as other3,
                            dccm_other4 as other4,
                            dccm_other5 as other5
                    FROM    retail.daily_customer_count_manual
                    WHERE   dccm_store = %s AND
                            dccm_file_date = %s
                """, (
                    request.ddsm_store, request.ddsm_file_date,
                    request.ddsm_store, request.ddsm_file_date,
                    request.ddsm_store, request.ddsm_file_date
                ))
                
                rows = cur.fetchall()
                data = []
                for row in rows:
                    data.append(DeptInputRow(
                        row_description=row[0],
                        restaurant=float(row[1]) if row[1] is not None else 0.0,
                        fuelgrocery=float(row[2]) if row[2] is not None else 0.0,
                        other3=float(row[3]) if row[3] is not None else 0.0,
                        other4=float(row[4]) if row[4] is not None else 0.0,
                        other5=float(row[5]) if row[5] is not None else 0.0
                    ))

                return DeptInputSelectResponse(
                    return_value=0,
                    error_message="",
                    data=data
                )

    except Exception as ex:
        logger.exception("Error in DeptInput Select")
        return DeptInputSelectResponse(
            return_value=1,
            error_message="Select Failed"
        )
