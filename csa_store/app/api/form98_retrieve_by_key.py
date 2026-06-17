from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.form98_retrieve_request import (
    Form98RetrieveByKeyRequest
)

router = APIRouter(
    prefix="/form98",
    tags=["Form98"]
)

@router.post("/retrievebykey")
def retrieve_by_key(
        request: Form98RetrieveByKeyRequest):

    try:

        with DBConnection() as conn:
            with conn.cursor() as cur:

                #
                # Validation 1
                # Invalid Store
                #

                if (
                    request.cb_store is None
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                #
                # Validation 2
                # Invalid Date
                #

                if (
                    request.cb_date is None
                ):

                    return {
                        "return_value": 2,
                        "error_message": "Invalid Date"
                    }

                #
                # Validation 3
                # Invalid Employee ID
                #

                if (
                    request.cb_employee_id is None
                    or
                    request.cb_employee_id == ""
                ):

                    return {
                        "return_value": 3,
                        "error_message": "Invalid Employee ID"
                    }

                #
                # Validation 4
                # Invalid Till
                #

                if (
                    request.cb_till is None
                ):

                    return {
                        "return_value": 4,
                        "error_message": "Invalid Till"
                    }

                #
                # Count Check
                #

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

                if count == 0:

                    return {
                        "return_value": 5,
                        "error_message": "Row Not Found"
                    }

                #
                # Retrieve Row
                #

                cur.execute("""
                    SELECT
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

                row = cur.fetchone()

                return {
                    "cb_store": row[0],
                    "cb_date": row[1],
                    "cb_employee_id": row[2],
                    "cb_till": row[3],
                    "cb_name": row[4],
                    "cb_sales": float(row[5]) if row[5] is not None else None,
                    "cb_voids": float(row[6]) if row[6] is not None else None,
                    "cb_returns": float(row[7]) if row[7] is not None else None,
                    "cb_checks": float(row[8]) if row[8] is not None else None,
                    "cb_gift_cards_tendered": float(row[9]) if row[9] is not None else None,
                    "cb_ebt": float(row[10]) if row[10] is not None else None,
                    "cb_credit_cards": float(row[11]) if row[11] is not None else None,
                    "cb_wic": float(row[12]) if row[12] is not None else None,
                    "cb_charges": float(row[13]) if row[13] is not None else None,
                    "cb_debit_cards": float(row[14]) if row[14] is not None else None,
                    "cb_vendor_coupons": float(row[15]) if row[15] is not None else None,
                    "cb_pfc_coupons": float(row[16]) if row[16] is not None else None,
                    "cb_cashier_over_short": float(row[17]) if row[17] is not None else None,
                    "cb_user": row[18],
                    "cb_promo_coupons": float(row[19]) if row[19] is not None else None,
                    "cb_miscellaneous": float(row[20]) if row[20] is not None else None,
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:

        return {
            "return_value": 1,
            "error_message": str(ex)
        }