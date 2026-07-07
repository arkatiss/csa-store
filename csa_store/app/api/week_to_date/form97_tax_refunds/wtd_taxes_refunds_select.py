import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_tax_refunds.wtd_taxes_refunds_select_schema import WTDTaxesRefundsSelectRequest, WTDTaxesRefundsSelectResponse, TaxRefundItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/form97_tax_refunds",
    tags=["Week To Date Form 97 Tax Refunds"]
)

@router.post("/wtd_taxes_refunds_select", response_model=WTDTaxesRefundsSelectResponse)
def csa_wtd_taxes_refunds_select(request: WTDTaxesRefundsSelectRequest):
    """
    Equivalent of:
    csa_WTDTaxesRefunds_Select
    """
    try:
        if request.wt_store is None:
            return WTDTaxesRefundsSelectResponse(
                return_value=1,
                error_message="Invalid Store",
                tax_refunds=[]
            )
            
        if request.wt_week_ending_date is None:
            return WTDTaxesRefundsSelectResponse(
                return_value=2,
                error_message="Invalid Date",
                tax_refunds=[]
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if row exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_taxes
                    WHERE wt_store = %s AND wt_week_ending_date = %s
                """, (request.wt_store, request.wt_week_ending_date))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return WTDTaxesRefundsSelectResponse(
                        return_value=3,
                        error_message="Row not found",
                        tax_refunds=[]
                    )

                # Retrieve amounts
                cur.execute("""
                    SELECT wt_tax_rate,
                           wt_refunds
                    FROM retail_accounting.wtd_taxes
                    WHERE wt_store = %s AND wt_week_ending_date = %s
                """, (request.wt_store, request.wt_week_ending_date))
                
                rows = cur.fetchall()
                tax_refunds = []
                for row in rows:
                    tax_refunds.append(TaxRefundItem(
                        wt_tax_rate=row[0] if row[0] is not None else "",
                        wt_refunds=float(row[1]) if row[1] is not None else 0.0
                    ))

                return WTDTaxesRefundsSelectResponse(
                    return_value=0,
                    error_message="",
                    tax_refunds=tax_refunds
                )

    except Exception as ex:
        logger.exception("Error in WTDTaxesRefunds_Select")
        return WTDTaxesRefundsSelectResponse(
            return_value=1,
            error_message="Select WTD Taxes Refunds Failed",
            tax_refunds=[]
        )
