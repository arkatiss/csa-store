import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_net_sales.wtd_net_sales_select_schema import WTDNetSalesSelectRequest, WTDNetSalesSelectResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/form97_net_sales",
    tags=["Week To Date Form 97 Net Sales"]
)

@router.post("/wtd_net_sales_select", response_model=WTDNetSalesSelectResponse)
def csa_wtd_net_sales_select(request: WTDNetSalesSelectRequest):
    """
    Equivalent of:
    csa_WTDNetSales_Select
    """
    try:
        if request.wns_store is None:
            return WTDNetSalesSelectResponse(
                return_value=1,
                error_message="Invalid Store"
            )
            
        if request.wns_week_ending_date is None:
            return WTDNetSalesSelectResponse(
                return_value=1,
                error_message="Invalid Week Ending Date"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if row exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_net_sales
                    WHERE wns_store = %s AND wns_week_ending_date = %s
                """, (request.wns_store, request.wns_week_ending_date))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return WTDNetSalesSelectResponse(
                        return_value=3,
                        error_message="Row not found"
                    )

                # Retrieve amounts
                cur.execute("""
                    SELECT wns_current_group_reading,
                           wns_previous_group_reading,
                           wns_gross_receipts,
                           wns_voids,
                           wns_refunds,
                           wns_tax_credits,
                           wns_store_coupons,
                           wns_other_sales,
                           wns_other_sales_description
                    FROM retail_accounting.wtd_net_sales
                    WHERE wns_store = %s AND wns_week_ending_date = %s
                """, (request.wns_store, request.wns_week_ending_date))
                
                row = cur.fetchone()
                if row:
                    return WTDNetSalesSelectResponse(
                        return_value=0,
                        error_message="",
                        wns_current_group_reading=float(row[0]) if row[0] is not None else 0.0,
                        wns_previous_group_reading=float(row[1]) if row[1] is not None else 0.0,
                        wns_gross_receipts=float(row[2]) if row[2] is not None else 0.0,
                        wns_voids=float(row[3]) if row[3] is not None else 0.0,
                        wns_refunds=float(row[4]) if row[4] is not None else 0.0,
                        wns_tax_credits=float(row[5]) if row[5] is not None else 0.0,
                        wns_store_coupons=float(row[6]) if row[6] is not None else 0.0,
                        wns_other_sales=float(row[7]) if row[7] is not None else 0.0,
                        wns_other_sales_description=row[8] if row[8] is not None else ""
                    )
                else:
                    return WTDNetSalesSelectResponse(
                        return_value=1,
                        error_message="Error retrieving data"
                    )

    except Exception as ex:
        logger.exception("Error in WTDNetSales_Select")
        return WTDNetSalesSelectResponse(
            return_value=1,
            error_message="Select WTD Net Sales Failed"
        )
