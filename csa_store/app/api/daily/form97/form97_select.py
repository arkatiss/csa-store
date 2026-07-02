import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form97.form97_select_schema import (
    Form97SelectRequest
)

from app.utils.daily.form97_helper import (
    get_week_ending_date
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form97",
    tags=["Form97"]
)


@router.post("/select")
def form97_select(
        request: Form97SelectRequest):
    """
    Equivalent of:

    csa_OfficeBalance_Select
    """

    try:

        #
        # VALIDATION
        #

        if request.ob_store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if request.ob_date is None:

            return {
                "return_value": 2,
                "error_message": "Invalid Date"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # WEEK ENDING DATE
                #

                try:

                    week_ending_date = (
                        get_week_ending_date(
                            cur,
                            request.tenant_id,
                            request.ob_store
                        )
                    )

                    print("week_ending_date =", week_ending_date)

                except Exception:

                    return {
                        "return_value": 3,
                        "error_message":
                            "Invalid Week Ending Date"
                    }

                #
                # CHECK RECORD EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_history.office_balance
                    WHERE tenant_id=%s
                    AND ob_store=%s
                    AND ob_date=%s
                """,
                (
                    str(request.tenant_id),
                    request.ob_store,
                    request.ob_date
                ))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 3,
                        "error_message":
                            "Row not found"
                    }

                #
                # FETCH DATA
                #

                cur.execute("""
                    SELECT
                        ob.ob_petty_cash_fund,
                        ob.ob_petty_cash_advances,

                        (
                            dsct.dsct_net_sales_amount +
                            dsct.dsct_net_receipts +
                            dsct.dsct_cashier_over_short -

                            (
                                dsct.dsct_dept_payouts +
                                dsct.dsct_cash_expense +
                                dsct.dsct_key_entered +
                                dsct.dsct_charge_sales
                            )

                            -
                            dsct.dsct_previous_deposits
                            -
                            dsct.dsct_actual_daily_deposits

                        ) AS dsct_final_cash_deposit,

                        ob.ob_cashier_over_short,
                        ob.ob_net_accountability,
                        ob.ob_currency_in_safe,
                        ob.ob_coin_in_safe,
                        ob.ob_currency_in_office,
                        ob.ob_coin_in_office,
                        ob.ob_checks,
                        ob.ob_returned_checks,
                        ob.ob_food_stamps,
                        ob.ob_bank_cards,
                        ob.ob_paid_outs_cd,
                        ob.ob_employee_loans,
                        ob.ob_register_tills,
                        ob.ob_atm_machine,
                        ob.ob_miscellaneous_1,
                        ob.ob_miscellaneous_1_description,
                        ob.ob_miscellaneous_2,
                        ob.ob_miscellaneous_2_description,
                        ob.ob_total_in_office,

                        (
                            ob.ob_total_in_office -
                            ob.ob_net_accountability
                        ) AS ob_office_over_short

                    FROM retail_history.office_balance ob

                    INNER JOIN
                    retail_accounting.daily_sales_cash_total dsct
                        ON ob.ob_store =
                           dsct.dsct_store
                        AND ob.tenant_id =
                           dsct.tenant_id

                    WHERE ob.tenant_id=%s
                    AND ob.ob_store=%s
                    AND ob.ob_date=%s
                    AND dsct.dsct_week_ending_date=%s
                """,
                (
                    str(request.tenant_id),
                    request.ob_store,
                    request.ob_date,
                    week_ending_date
                ))

                row = cur.fetchone()

                return {
                    "return_value": 0,
                    "data": {
                        "ob_petty_cash_fund":
                            row[0],
                        "ob_petty_cash_advances":
                            row[1],
                        "dsct_final_cash_deposit":
                            row[2],
                        "ob_cashier_over_short":
                            row[3],
                        "ob_net_accountability":
                            row[4],
                        "ob_currency_in_safe":
                            row[5],
                        "ob_coin_in_safe":
                            row[6],
                        "ob_currency_in_office":
                            row[7],
                        "ob_coin_in_office":
                            row[8],
                        "ob_checks":
                            row[9],
                        "ob_returned_checks":
                            row[10],
                        "ob_food_stamps":
                            row[11],
                        "ob_bank_cards":
                            row[12],
                        "ob_paid_outs_cd":
                            row[13],
                        "ob_employee_loans":
                            row[14],
                        "ob_register_tills":
                            row[15],
                        "ob_atm_machine":
                            row[16],
                        "ob_miscellaneous_1":
                            row[17],
                        "ob_miscellaneous_1_description":
                            row[18],
                        "ob_miscellaneous_2":
                            row[19],
                        "ob_miscellaneous_2_description":
                            row[20],
                        "ob_total_in_office":
                            row[21],
                        "ob_office_over_short":
                            row[22]
                    }
                }

    except Exception as ex:

        logger.exception(
            "Error in Form97 Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }