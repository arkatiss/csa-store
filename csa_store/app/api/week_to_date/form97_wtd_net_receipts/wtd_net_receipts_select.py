import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_wtd_net_receipts.wtd_net_receipts_select_schema import WTDNetReceiptsSelectRequest, WTDNetReceiptsSelectResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/form97_wtd_net_receipts",
    tags=["Week To Date Form 97 WTD Net Receipts"]
)

@router.post("/wtd_net_receipts_select", response_model=WTDNetReceiptsSelectResponse)
def csa_wtd_net_receipts_select(request: WTDNetReceiptsSelectRequest):
    """
    Equivalent of:
    csa_WTDNetReceipts_Select
    """
    try:
        if request.wnr_store is None:
            return WTDNetReceiptsSelectResponse(
                return_value=1,
                error_message="Invalid Store"
            )
            
        if request.wnr_week_ending_date is None:
            return WTDNetReceiptsSelectResponse(
                return_value=1,
                error_message="Invalid Week Ending Date"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if row exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_net_receipts
                    WHERE wnr_store = %s AND wnr_week_ending_date = %s
                """, (request.wnr_store, request.wnr_week_ending_date))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return WTDNetReceiptsSelectResponse(
                        return_value=3,
                        error_message="Row not found"
                    )

                # Retrieve amounts
                cur.execute("""
                    SELECT wnr_form111_total,
                           wnr_ar_collected,
                           wnr_mo_receipts,
                           wnr_nbr_of_mo
                    FROM retail_accounting.wtd_net_receipts
                    WHERE wnr_store = %s AND wnr_week_ending_date = %s
                """, (request.wnr_store, request.wnr_week_ending_date))
                
                row = cur.fetchone()
                if row:
                    return WTDNetReceiptsSelectResponse(
                        return_value=0,
                        error_message="",
                        wnr_form111_total=float(row[0]) if row[0] is not None else 0.0,
                        wnr_ar_collected=float(row[1]) if row[1] is not None else 0.0,
                        wnr_mo_receipts=float(row[2]) if row[2] is not None else 0.0,
                        wnr_nbr_of_mo=int(row[3]) if row[3] is not None else 0
                    )
                else:
                    return WTDNetReceiptsSelectResponse(
                        return_value=1,
                        error_message="Error retrieving data"
                    )

    except Exception as ex:
        logger.exception("Error in WTDNetReceipts_Select")
        return WTDNetReceiptsSelectResponse(
            return_value=1,
            error_message="Select WTD Net Receipts Failed"
        )
