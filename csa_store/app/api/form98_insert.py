# form98_insert.py

from fastapi import APIRouter
from app.core.db_utils import DBConnection

router = APIRouter(
    prefix="/form98",
    tags=["Form98"]
)

@router.post("/insert")
def insert_form98(request: Form98Request):

    # Validations

    if not request.cb_store:
        return {
            "return_value": 1,
            "error_message": "Invalid Store"
        }

    if not request.cb_employee_id:
        return {
            "return_value": 1,
            "error_message": "Invalid Employee ID"
        }

    try:

        with DBConnection() as conn:
            with conn.cursor() as cur:

                # Duplicate Check

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_history.cashier_balance
                    WHERE cb_store=%s
                    AND cb_date=%s
                    AND cb_employee_id=%s
                    AND cb_till=%s
                """,
                (
                    request.cb_store,
                    request.cb_date,
                    request.cb_employee_id,
                    request.cb_till
                ))

                count = cur.fetchone()[0]

                if count > 0:
                    return {
                        "return_value": 1,
                        "error_message": "Row Already Exists"
                    }

                # Insert

                cur.execute("""
                    INSERT INTO retail_history.cashier_balance
                    (
                        tenant_id,
                        cb_store,
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
                    )
                    VALUES
                    (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        %s,%s
                    )
                """,
                (
                    request.tenant_id,
                    request.cb_store,
                    request.cb_date,
                    request.cb_employee_id,
                    request.cb_till,
                    request.cb_name,
                    request.cb_sales,
                    request.cb_voids,
                    request.cb_returns,
                    request.cb_checks,
                    request.cb_gift_cards_tendered,
                    request.cb_ebt,
                    request.cb_credit_cards,
                    request.cb_wic,
                    request.cb_charges,
                    request.cb_debit_cards,
                    request.cb_vendor_coupons,
                    request.cb_pfc_coupons,
                    request.cb_cashier_over_short,
                    request.cb_user,
                    request.cb_promo_coupons,
                    request.cb_miscellaneous
                ))

        return {
            "return_value": 0,
            "error_message": ""
        }

    except Exception as ex:

        return {
            "return_value": 1,
            "error_message": str(ex)
        }