import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.reports.daily.form98_retrieve_by_day_schema import Form98RetrieveByDayRequest, Form98RetrieveByDayResponse, Form98RetrieveByDayItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports/daily",
    tags=["Reports Daily Form 98"]
)

@router.post("/form98_retrieve_by_day", response_model=Form98RetrieveByDayResponse)
def csa_form98_retrieve_by_day(request: Form98RetrieveByDayRequest):
    """
    Equivalent of:
    csa_Form98_RetrieveByDay
    """
    try:
        if request.cb_store is None or str(request.cb_store).strip() == '':
            return Form98RetrieveByDayResponse(
                return_value=1,
                error_message="Invalid Store",
                data=None
            )
            
        if request.cb_date is None or str(request.cb_date).strip() == '':
            return Form98RetrieveByDayResponse(
                return_value=1,
                error_message="Invalid Date",
                data=None
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Retrieve values
                cur.execute("""
                    SELECT 
                        cb_date,
                        cb_employee_id,
                        cb_till,
                        cb_name,
                        cb_sales,
                        cb_voids,
                        cb_returns,
                        cb_checks,
                        cb_gift_cards_tendered,
                        cb_ebt,
                        cb_credit_cards,
                        cb_wic,
                        cb_charges,
                        cb_debit_cards,
                        cb_vendor_coupons,
                        cb_pfc_coupons,
                        cb_cashier_over_short,
                        cb_user,
                        cb_promo_coupons,
                        cb_miscellaneous
                    FROM retail_history.cashier_balance
                    WHERE cb_store = %s AND cb_date = %s
                """, (request.cb_store, request.cb_date))
                
                rows = cur.fetchall()
                data = []
                for row in rows:
                    item = Form98RetrieveByDayItem(
                        cb_date=row[0],
                        cb_employee_id=row[1],
                        cb_till=row[2],
                        cb_name=row[3],
                        cb_sales=row[4],
                        cb_voids=row[5],
                        cb_returns=row[6],
                        cb_checks=row[7],
                        cb_gift_cards_tendered=row[8],
                        cb_ebt=row[9],
                        cb_credit_cards=row[10],
                        cb_wic=row[11],
                        cb_charges=row[12],
                        cb_debit_cards=row[13],
                        cb_vendor_coupons=row[14],
                        cb_pfc_coupons=row[15],
                        cb_cashier_over_short=row[16],
                        cb_user=row[17],
                        cb_promo_coupons=row[18],
                        cb_miscellaneous=row[19]
                    )
                    data.append(item)
                    
                return Form98RetrieveByDayResponse(
                    return_value=0,
                    error_message="",
                    data=data
                )

    except Exception as ex:
        logger.exception("Error in Form98_RetrieveByDay")
        return Form98RetrieveByDayResponse(
            return_value=1,
            error_message="Retrieve By Day Failed",
            data=None
        )
