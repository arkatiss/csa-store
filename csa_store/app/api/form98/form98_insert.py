from fastapi import APIRouter
from datetime import datetime, timedelta

from app.schemas.form98.form98_request import Form98InsertRequest
from app.core.db_utils import DBConnection

from app.utils.form98_helper import (
    sql_weekday,
    get_week_ending_date,
    get_last_date_open,
    update_dsc_with_form98,
    update_wcb_with_form98,
    insert_cashier_balance,
    insert_audit
)

router = APIRouter(
    prefix="/form98",
    tags=["Form98"]
)


@router.post("/insert")
def form98_insert(
        request: Form98InsertRequest):

    conn = None

    try:

        with DBConnection() as conn:
            with conn.cursor() as cur:

                if request.cb_store is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                cur.execute("""
                    SELECT
                        tenant_id,
                        sc_eow_last_run,
                        sc_eod_last_run,
                        sc_open_days
                    FROM retail_accounting.store_configuration
                    WHERE sc_store=%s
                """,
                            (
                                request.cb_store,
                            ))

                store_cfg = cur.fetchone()

                if not store_cfg:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                tenant_id = store_cfg[0]
                sc_eow_last_run = store_cfg[1]

                sc_eow_last_run = (
                    sc_eow_last_run.replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                )

                if sql_weekday(
                        sc_eow_last_run
                ) == 1:

                    week_ending_date = (
                        sc_eow_last_run
                    )

                else:

                    week_ending_date = (
                            sc_eow_last_run +
                            timedelta(
                                days=
                                (
                                        8 -
                                        sql_weekday(
                                            sc_eow_last_run
                                        )
                                )
                            )
                    )

                last_week_ending_date = (
                        week_ending_date -
                        timedelta(days=7)
                )

                if (
                        request.cb_date is None
                        or
                        request.cb_date <=
                        last_week_ending_date.date()
                        or
                        request.cb_date >
                        (
                                week_ending_date +
                                timedelta(days=1)
                        ).date()
                ):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                validations = [
                    (
                        request.cb_employee_id,
                        "Invalid Employee ID"
                    ),
                    (
                        request.cb_till,
                        "Invalid Till Number"
                    ),
                    (
                        request.cb_name,
                        "Invalid Employee Name"
                    ),
                    (
                        request.cb_sales,
                        "Invalid Sales"
                    ),
                    (
                        request.cb_voids,
                        "Invalid Voids"
                    ),
                    (
                        request.cb_returns,
                        "Invalid Returns"
                    ),
                    (
                        request.cb_checks,
                        "Invalid Checks"
                    ),
                    (
                        request.cb_gift_cards_tendered,
                        "Invalid Gift Cards"
                    ),
                    (
                        request.cb_ebt,
                        "Invalid EBT"
                    ),
                    (
                        request.cb_credit_cards,
                        "Invalid Credit Cards"
                    ),
                    (
                        request.cb_wic,
                        "Invalid WIC"
                    ),
                    (
                        request.cb_charges,
                        "Invalid Charges"
                    ),
                    (
                        request.cb_debit_cards,
                        "Invalid Debit Cards"
                    ),
                    (
                        request.cb_vendor_coupons,
                        "Invalid Vendor Coupons"
                    ),
                    (
                        request.cb_pfc_coupons,
                        "Invalid PFC_Coupons"
                    ),
                    (
                        request.cb_cashier_over_short,
                        "Invalid Cashier Over/Short"
                    ),
                    (
                        request.cb_user,
                        "Invalid User"
                    ),
                    (
                        request.cb_promo_coupons,
                        "Invalid Promo Coupons"
                    ),
                    (
                        request.cb_miscellaneous,
                        "Invalid Miscellaneous"
                    )
                ]

                for value, message in validations:

                    if value is None:
                        return {
                            "return_value": 1,
                            "error_message": message
                        }

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

                if count == 1:
                    return {
                        "return_value": 1,
                        "error_message": "Row Already Exists"
                    }

                insert_cashier_balance(
                    cur,
                    tenant_id,
                    request
                )

                cur.execute("""
                    SELECT
                        COALESCE(
                            SUM(
                                cb_cashier_over_short
                            ),
                            0
                        )
                    FROM retail_history.cashier_balance
                    WHERE cb_store=%s
                    AND cb_date > %s
                    AND cb_date <= %s
                """,
                            (
                                request.cb_store,
                                last_week_ending_date.date(),
                                week_ending_date.date()
                            ))

                ob_cashier_over_short = (
                    cur.fetchone()[0]
                )

                cur.execute("""
                    UPDATE retail.office_balance
                    SET
                        ob_cashier_over_short=%s,
                        ob_net_accountability=
                            ob_petty_cash_fund
                            +
                            ob_petty_cash_advances
                            +
                            %s
                    WHERE ob_store=%s
                """,
                            (
                                ob_cashier_over_short,
                                ob_cashier_over_short,
                                request.cb_store
                            ))

                update_dsc_with_form98(
                    cur,
                    request.cb_store,
                    week_ending_date
                )

                update_wcb_with_form98(
                    cur,
                    request.cb_store
                )

                conn.commit()

                insert_audit(
                    cur,
                    tenant_id,
                    request
                )

                conn.commit()

                return {
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:

        return {
            "return_value": 1,
            "error_message": str(ex)
        }
