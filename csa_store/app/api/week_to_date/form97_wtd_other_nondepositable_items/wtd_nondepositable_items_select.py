import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_nondepositable_items.wtd_nondepositable_items_select_schema import WTDNonDepositableItemsSelectRequest, WTDNonDepositableItemsSelectResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/wtd_non_depositable_items",
    tags=["Week To Date Other Non Depositable Items"]
)

@router.post("/wtd_nondepositable_items_select", response_model=WTDNonDepositableItemsSelectResponse)
def csa_wtd_nondepositable_items_select(request: WTDNonDepositableItemsSelectRequest):
    """
    Equivalent of:
    csa_WTDNonDepositableItems_Select
    """
    try:
        if request.wndi_store is None:
            return WTDNonDepositableItemsSelectResponse(
                return_value=1,
                error_message="Invalid Store"
            )
            
        if request.wndi_week_ending_date is None:
            return WTDNonDepositableItemsSelectResponse(
                return_value=1,
                error_message="Invalid Week Ending Date"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if row exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_non_depositable_items
                    WHERE wndi_store = %s AND wndi_week_ending_date = %s
                """, (request.wndi_store, request.wndi_week_ending_date))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return WTDNonDepositableItemsSelectResponse(
                        return_value=3,
                        error_message="Row not found"
                    )

                # Retrieve values
                cur.execute("""
                    SELECT 	wndi_cash_savers,
                            wndi_gift_certificates,
                            wndi_vendor_coupons,
                            wndi_third_party_rx,
                            wndi_miscellaneous,
                            wndi_pfc_coupons,
                            wndi_elec_gbax_coupons
                    FROM	retail_accounting.wtd_non_depositable_items
                    WHERE	wndi_store = %s AND wndi_week_ending_date = %s
                """, (request.wndi_store, request.wndi_week_ending_date))
                
                row = cur.fetchone()
                if row:
                    return WTDNonDepositableItemsSelectResponse(
                        return_value=0,
                        error_message="",
                        wndi_cash_savers=row[0],
                        wndi_gift_certificates=row[1],
                        wndi_vendor_coupons=row[2],
                        wndi_third_party_rx=row[3],
                        wndi_miscellaneous=row[4],
                        wndi_pfc_coupons=row[5],
                        wndi_elec_gbax_coupons=row[6]
                    )
                else:
                    return WTDNonDepositableItemsSelectResponse(
                        return_value=1,
                        error_message="Select WTD Non Depositable Items Failed"
                    )

    except Exception as ex:
        logger.exception("Error in WTDNonDepositableItems_Select")
        return WTDNonDepositableItemsSelectResponse(
            return_value=1,
            error_message="Select WTD Non Depositable Items Failed"
        )
