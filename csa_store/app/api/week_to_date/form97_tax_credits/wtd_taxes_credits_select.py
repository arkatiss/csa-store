import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_tax_credits.wtd_taxes_credits_select_schema import WTDTaxesCreditsSelectRequest, WTDTaxesCreditsSelectResponse, TaxCreditItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/form97_tax_credits",
    tags=["Week To Date Form 97 Tax Credits"]
)

@router.post("/wtd_taxes_credits_select", response_model=WTDTaxesCreditsSelectResponse)
def csa_wtd_taxes_credits_select(request: WTDTaxesCreditsSelectRequest):
    """
    Equivalent of:
    csa_WTDTaxesCredits_Select
    """
    try:
        if request.wt_store is None:
            return WTDTaxesCreditsSelectResponse(
                return_value=1,
                error_message="Invalid Store",
                tax_credits=[]
            )
            
        if request.wt_week_ending_date is None:
            return WTDTaxesCreditsSelectResponse(
                return_value=2,
                error_message="Invalid Date",
                tax_credits=[]
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
                    return WTDTaxesCreditsSelectResponse(
                        return_value=3,
                        error_message="Row not found",
                        tax_credits=[]
                    )

                # Retrieve amounts
                cur.execute("""
                    SELECT wt_tax_rate,
                           wt_credits
                    FROM retail_accounting.wtd_taxes
                    WHERE wt_store = %s AND wt_week_ending_date = %s
                """, (request.wt_store, request.wt_week_ending_date))
                
                rows = cur.fetchall()
                tax_credits = []
                for row in rows:
                    tax_credits.append(TaxCreditItem(
                        wt_tax_rate=row[0] if row[0] is not None else "",
                        wt_credits=float(row[1]) if row[1] is not None else 0.0
                    ))

                return WTDTaxesCreditsSelectResponse(
                    return_value=0,
                    error_message="",
                    tax_credits=tax_credits
                )

    except Exception as ex:
        logger.exception("Error in WTDTaxesCredits_Select")
        return WTDTaxesCreditsSelectResponse(
            return_value=1,
            error_message="Select WTD Taxes Credits Failed",
            tax_credits=[]
        )
