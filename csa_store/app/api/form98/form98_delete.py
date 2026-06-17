from datetime import timedelta

from fastapi import APIRouter

from app.schemas.form98.form98_delete_request import (
    Form98DeleteRequest
)

from app.core.db_utils import DBConnection

from app.utils.form98_helper import (
    sql_weekday,
    update_dsc_with_form98,
    update_wcb_with_form98,
    insert_delete_audit
)

router = APIRouter(
    prefix="/form98",
    tags=["Form98"]
)


@router.delete("/delete")
def form98_delete(
        request: Form98DeleteRequest):

    try:

        with DBConnection() as conn:
            with conn.cursor() as cur:

                #
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
                # Get Store Configuration
                #

                cur.execute("""
                    SELECT
                        tenant_id,
                        sc_eow_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store=%s
                """,
                (
                    request.cb_store,
                ))

                store_row = cur.fetchone()

                if not store_row:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                tenant_id = store_row[0]
                sc_eow_last_run = store_row[1]

                #
                # Week Ending Date Logic
                #

                if sql_weekday(sc_eow_last_run) == 1:

                    week_ending_date = (
                        sc_eow_last_run.date()
                    )

                else:

                    week_ending_date = (
                        sc_eow_last_run +
                        timedelta(
                            days=(
                                8 -
                                sql_weekday(
                                    sc_eow_last_run
                                )
                            )
                        )
                    ).date()

                last_week_ending_date = (
                    week_ending_date -
                    timedelta(days=7)
                )

                #
                # Invalid Date
                #

                if (
                    request.cb_date is None
                    or
                    request.cb_date <= last_week_ending_date
                    or
                    request.cb_date >
                    (
                        week_ending_date +
                        timedelta(days=1)
                    )
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                #
                # Invalid Employee ID
                #

                if (
                    request.cb_employee_id is None
                    or
                    request.cb_employee_id == ""
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Employee ID"
                    }

                #
                # Invalid Till
                #

                if (
                    request.cb_till is None
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Till Number"
                    }

                #
                # Invalid User
                #

                if (
                    request.cb_user is None
                    or
                    request.cb_user == ""
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid User"
                    }

                #
                # Delete Record
                #

                cur.execute("""
                    DELETE
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

                #
                # Update Office Balance
                #

                cur.execute("""
                    SELECT
                        COALESCE(
                            SUM(cb_cashier_over_short),
                            0
                        )
                    FROM retail_history.cashier_balance
                    WHERE cb_store=%s
                    AND cb_date > %s
                    AND cb_date <= %s
                """,
                (
                    request.cb_store,
                    last_week_ending_date,
                    week_ending_date
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
                            -
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

                #
                # Update DSC
                #

                update_dsc_with_form98(
                    cur,
                    request.cb_store,
                    week_ending_date
                )

                #
                # Update WCB
                #

                update_wcb_with_form98(
                    cur,
                    request.cb_store
                )

                #
                # Audit
                #

                insert_delete_audit(
                    cur,
                    tenant_id,
                    request
                )

                return {
                    "return_value": 0,
                    "error_message": ""
                }

    except Exception as ex:

        return {
            "return_value": 1,
            "error_message": str(ex)
        }