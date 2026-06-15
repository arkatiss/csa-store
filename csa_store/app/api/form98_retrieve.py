from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.form98_request import (
    Form98InsertRequest
)

from app.utils.form98_helper import (
    calculate_week_ending_date,
    calculate_last_date_open,
    sqlserver_weekday
)

from datetime import datetime, timedelta

router = APIRouter(
    prefix="/form98",
    tags=["Form98"]
)

def get_store_configuration(
        cur,
        store):

    cur.execute("""
        SELECT
            tenant_id,
            sc_eow_last_run,
            sc_eod_last_run,
            sc_open_days
        FROM retail_accounting.store_configuration
        WHERE sc_store=%s
    """,
    (store,))

    return cur.fetchone()

def check_duplicate_record(
        cur,
        store,
        cb_date,
        employee_id,
        till):

    cur.execute("""
        SELECT COUNT(*)
        FROM retail.cashier_balance
        WHERE cb_store=%s
        AND cb_date=%s
        AND cb_employee_id=%s
        AND cb_till=%s
    """,
    (
        store,
        cb_date,
        employee_id,
        till
    ))

    return cur.fetchone()[0]

def insert_cashier_balance(
        cur,
        tenant_id,
        request):
    pass



def update_office_balance(
        cur,
        store,
        last_week_ending_date,
        week_ending_date):

    cur.execute("""
        SELECT
            COALESCE(
                SUM(cb_cashier_over_short),
                0
            )
        FROM retail.cashier_balance
        WHERE cb_store=%s
        AND cb_date > %s
        AND cb_date <= %s
    """,
    (
        store,
        last_week_ending_date,
        week_ending_date
    ))

    over_short = cur.fetchone()[0]

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
        over_short,
        over_short,
        store
    ))

@router.post("/insert")
def form98_insert(
        request: Form98InsertRequest):
    try:
        with DBConnection() as conn:
            conn.autocommit = False

            with conn.cursor() as cur:
    if request.cb_store is None:
        return {
            "return_value": 1,
            "error_message": "Invalid Store"
        }

    store_cfg = get_store_configuration(
        cur,
        request.cb_store
    )

    if not store_cfg:
        return {
            "return_value": 1,
            "error_message": "Invalid Store"
        }

    tenant_id = store_cfg[0]
    sc_eow_last_run = store_cfg[1]
    sc_eod_last_run = store_cfg[2]
    sc_open_days = store_cfg[3]

    week_ending_date = calculate_week_ending_date(
        sc_eow_last_run
    )

    last_week_ending_date = (
            week_ending_date
            -
            timedelta(days=7)
    )

    if (
            request.cb_date <= last_week_ending_date.date()
            or
            request.cb_date >
            (
                    week_ending_date
                    +
                    timedelta(days=1)
            ).date()
    ):
        return {
            "return_value": 1,
            "error_message": "Invalid Date"
        }

    count = check_duplicate_record(
        cur,
        request.cb_store,
        request.cb_date,
        request.cb_employee_id,
        request.cb_till
    )

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

    update_office_balance(
        cur,
        request.cb_store,
        last_week_ending_date.date(),
        week_ending_date.date()
    )



