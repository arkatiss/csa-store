import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.reports.weekly.form98_totals_by_day_schema import Form98TotalsByDayRequest, Form98TotalsByDayResponse, Form98TotalsByDayItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports/weekly",
    tags=["Reports Weekly Form 98 Totals"]
)

@router.post("/form98_totals_by_day", response_model=Form98TotalsByDayResponse)
def csa_form98_totals_by_day(request: Form98TotalsByDayRequest):
    """
    Equivalent of:
    csa_Form98_TotalsByDay
    """
    try:
        if request.cb_store is None or str(request.cb_store).strip() == '':
            return Form98TotalsByDayResponse(
                return_value=1,
                error_message="Invalid Store",
                data=None
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Retrieve values
                cur.execute("""
                    SELECT 
                        cb_date,
                        SUM(cb_sales) AS cb_sales,
                        SUM(cb_voids) AS cb_voids,
                        SUM(cb_returns) AS cb_returns,
                        SUM(cb_checks) AS cb_checks,
                        SUM(cb_gift_cards_tendered) AS cb_gift_cards_tendered,
                        SUM(cb_ebt) AS cb_ebt,
                        SUM(cb_credit_cards) AS cb_credit_cards,
                        SUM(cb_wic) AS cb_wic,
                        SUM(cb_charges) AS cb_charges,
                        SUM(cb_debit_cards) AS cb_debit_cards,
                        SUM(cb_vendor_coupons) AS cb_vendor_coupons,
                        SUM(cb_pfc_coupons) AS cb_pfc_coupons,
                        SUM(cb_cashier_over_short) AS cb_cashier_over_short,
                        SUM(cb_promo_coupons) AS cb_promo_coupons,
                        SUM(cb_miscellaneous) AS cb_miscellaneous
                    FROM retail_history.cashier_balance
                    WHERE cb_store = %s
                    GROUP BY cb_date
                    ORDER BY cb_date
                """, (request.cb_store,))
                
                rows = cur.fetchall()
                data = []
                for row in rows:
                    item = Form98TotalsByDayItem(
                        cb_date=row[0],
                        cb_sales=row[1],
                        cb_voids=row[2],
                        cb_returns=row[3],
                        cb_checks=row[4],
                        cb_gift_cards_tendered=row[5],
                        cb_ebt=row[6],
                        cb_credit_cards=row[7],
                        cb_wic=row[8],
                        cb_charges=row[9],
                        cb_debit_cards=row[10],
                        cb_vendor_coupons=row[11],
                        cb_pfc_coupons=row[12],
                        cb_cashier_over_short=row[13],
                        cb_promo_coupons=row[14],
                        cb_miscellaneous=row[15]
                    )
                    data.append(item)
                    
                return Form98TotalsByDayResponse(
                    return_value=0,
                    error_message="",
                    data=data
                )

    except Exception as ex:
        logger.exception("Error in Form98_TotalsByDay")
        return Form98TotalsByDayResponse(
            return_value=1,
            error_message="Select Failed",
            data=None
        )
