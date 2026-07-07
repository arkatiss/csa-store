import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.form97_tax_voids.wtd_taxes_voids_select_schema import WTDTaxesVoidsSelectRequest, WTDTaxesVoidsSelectResponse, TaxVoidItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/form97_tax_voids",
    tags=["Week To Date Form 97 Tax Voids"]
)

@router.post("/wtd_taxes_voids_select", response_model=WTDTaxesVoidsSelectResponse)
def csa_wtd_taxes_voids_select(request: WTDTaxesVoidsSelectRequest):
    """
    Equivalent of:
    csa_WTDTaxesVoids_Select
    """
    try:
        if request.wt_store is None:
            return WTDTaxesVoidsSelectResponse(
                return_value=1,
                error_message="Invalid Store",
                tax_voids=[]
            )
            
        if request.wt_week_ending_date is None:
            return WTDTaxesVoidsSelectResponse(
                return_value=2,
                error_message="Invalid Date",
                tax_voids=[]
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
                    return WTDTaxesVoidsSelectResponse(
                        return_value=3,
                        error_message="Row not found",
                        tax_voids=[]
                    )

                # Retrieve amounts
                cur.execute("""
                    SELECT wt_tax_rate,
                           wt_voids
                    FROM retail_accounting.wtd_taxes
                    WHERE wt_store = %s AND wt_week_ending_date = %s
                """, (request.wt_store, request.wt_week_ending_date))
                
                rows = cur.fetchall()
                tax_voids = []
                for row in rows:
                    tax_voids.append(TaxVoidItem(
                        wt_tax_rate=row[0] if row[0] is not None else "",
                        wt_voids=float(row[1]) if row[1] is not None else 0.0
                    ))

                return WTDTaxesVoidsSelectResponse(
                    return_value=0,
                    error_message="",
                    tax_voids=tax_voids
                )

    except Exception as ex:
        logger.exception("Error in WTDTaxesVoids_Select")
        return WTDTaxesVoidsSelectResponse(
            return_value=1,
            error_message="Select WTD Taxes Voids Failed",
            tax_voids=[]
        )
