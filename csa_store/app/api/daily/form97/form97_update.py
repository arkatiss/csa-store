import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form97.form97_update_schema import (
    Form97UpdateRequest
)

from app.utils.daily.form97_helper import (
    insert_form97_audit,
    audit_if_changed,
    audit_if_changed_with_null_support,
    calculate_net_accountability,
    calculate_total_in_office
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form97",
    tags=["Form97"]
)


@router.put("/update")
def form97_update(
        request: Form97UpdateRequest):
    """
    Equivalent of:

    csa_OfficeBalance_Update
    """

    conn = None

    try:

        #
        # VALIDATIONS
        #

        if request.ob_store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if request.ob_date is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Date"
            }

        if (
            request.user is None
            or
            request.user.strip() == ""
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid User"
            }

        validation_map = [
            (
                request.ob_petty_cash_advances,
                "Invalid Petty Cash Advances"
            ),
            (
                request.ob_currency_in_safe,
                "Invalid Currency In Safe"
            ),
            (
                request.ob_coin_in_safe,
                "Invalid Coin In Safe"
            ),
            (
                request.ob_currency_in_office,
                "Invalid Currency In Office"
            ),
            (
                request.ob_coin_in_office,
                "Invalid Coin In Office"
            ),
            (
                request.ob_checks,
                "Invalid Checks"
            ),
            (
                request.ob_returned_checks,
                "Invalid Returned Checks"
            ),
            (
                request.ob_food_stamps,
                "Invalid Food Stamps"
            ),
            (
                request.ob_bank_cards,
                "Invalid Bank Cards"
            ),
            (
                request.ob_paid_outs_cd,
                "Invalid Paid Outs CD"
            ),
            (
                request.ob_employee_loans,
                "Invalid Employee Loans"
            ),
            (
                request.ob_register_tills,
                "Invalid Register Tills"
            ),
            (
                request.ob_atm_machine,
                "Invalid ATM Machine"
            ),
            (
                request.ob_miscellaneous_1,
                "Invalid Miscellaneous 1"
            ),
            (
                request.ob_miscellaneous_2,
                "Invalid Miscellaneous 2"
            )
        ]

        for value, error_message in validation_map:

            if value is None:

                return {
                    "return_value": 1,
                    "error_message": error_message
                }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # ROW EXISTS
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
                        "return_value": 1,
                        "error_message": "Row Not Found"
                    }

                #
                # FETCH OLD VALUES
                #

                cur.execute("""
                    SELECT
                        ob_petty_cash_fund,
                        ob_cashier_over_short,

                        ob_petty_cash_advances,
                        ob_currency_in_safe,
                        ob_coin_in_safe,
                        ob_currency_in_office,
                        ob_coin_in_office,
                        ob_checks,
                        ob_returned_checks,
                        ob_food_stamps,
                        ob_bank_cards,
                        ob_paid_outs_cd,
                        ob_employee_loans,
                        ob_register_tills,
                        ob_atm_machine,
                        ob_miscellaneous_1,
                        ob_miscellaneous_1_description,
                        ob_miscellaneous_2,
                        ob_miscellaneous_2_description
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

                row = cur.fetchone()

                (
                    petty_cash_fund,
                    cashier_over_short,

                    old_petty_cash_advances,
                    old_currency_in_safe,
                    old_coin_in_safe,
                    old_currency_in_office,
                    old_coin_in_office,
                    old_checks,
                    old_returned_checks,
                    old_food_stamps,
                    old_bank_cards,
                    old_paid_outs_cd,
                    old_employee_loans,
                    old_register_tills,
                    old_atm_machine,
                    old_misc1,
                    old_misc1_desc,
                    old_misc2,
                    old_misc2_desc
                ) = row

                #
                # NO UPDATES DETECTED
                #

                if (
                    old_petty_cash_advances == request.ob_petty_cash_advances
                    and old_currency_in_safe == request.ob_currency_in_safe
                    and old_coin_in_safe == request.ob_coin_in_safe
                    and old_currency_in_office == request.ob_currency_in_office
                    and old_coin_in_office == request.ob_coin_in_office
                    and old_checks == request.ob_checks
                    and old_returned_checks == request.ob_returned_checks
                    and old_food_stamps == request.ob_food_stamps
                    and old_bank_cards == request.ob_bank_cards
                    and old_paid_outs_cd == request.ob_paid_outs_cd
                    and old_employee_loans == request.ob_employee_loans
                    and old_register_tills == request.ob_register_tills
                    and old_atm_machine == request.ob_atm_machine
                    and old_misc1 == request.ob_miscellaneous_1
                    and old_misc1_desc == request.ob_miscellaneous_1_description
                    and old_misc2 == request.ob_miscellaneous_2
                    and old_misc2_desc == request.ob_miscellaneous_2_description
                ):

                    return {
                        "return_value": 1,
                        "error_message": "No Updates Detected"
                    }

                #
                # CALCULATIONS
                #

                net_accountability = (
                    calculate_net_accountability(
                        petty_cash_fund,
                        request.ob_petty_cash_advances,
                        cashier_over_short
                    )
                )

                total_in_office = (
                    calculate_total_in_office(
                        request.ob_currency_in_safe,
                        request.ob_coin_in_safe,
                        request.ob_currency_in_office,
                        request.ob_coin_in_office,
                        request.ob_checks,
                        request.ob_returned_checks,
                        request.ob_food_stamps,
                        request.ob_bank_cards,
                        request.ob_paid_outs_cd,
                        request.ob_employee_loans,
                        request.ob_register_tills,
                        request.ob_atm_machine,
                        request.ob_miscellaneous_1,
                        request.ob_miscellaneous_2
                    )
                )

                #
                # UPDATE OFFICE BALANCE
                #

                cur.execute("""
                    UPDATE retail_history.office_balance
                    SET
                        ob_petty_cash_advances=%s,
                        ob_net_accountability=%s,

                        ob_currency_in_safe=%s,
                        ob_coin_in_safe=%s,

                        ob_currency_in_office=%s,
                        ob_coin_in_office=%s,

                        ob_checks=%s,
                        ob_returned_checks=%s,

                        ob_food_stamps=%s,
                        ob_bank_cards=%s,

                        ob_paid_outs_cd=%s,
                        ob_employee_loans=%s,

                        ob_register_tills=%s,
                        ob_atm_machine=%s,

                        ob_miscellaneous_1=%s,
                        ob_miscellaneous_1_description=%s,

                        ob_miscellaneous_2=%s,
                        ob_miscellaneous_2_description=%s,

                        ob_total_in_office=%s
                    WHERE tenant_id=%s
                    AND ob_store=%s
                    AND ob_date=%s
                """,
                (
                    request.ob_petty_cash_advances,
                    net_accountability,

                    request.ob_currency_in_safe,
                    request.ob_coin_in_safe,

                    request.ob_currency_in_office,
                    request.ob_coin_in_office,

                    request.ob_checks,
                    request.ob_returned_checks,

                    request.ob_food_stamps,
                    request.ob_bank_cards,

                    request.ob_paid_outs_cd,
                    request.ob_employee_loans,

                    request.ob_register_tills,
                    request.ob_atm_machine,

                    request.ob_miscellaneous_1,
                    request.ob_miscellaneous_1_description,

                    request.ob_miscellaneous_2,
                    request.ob_miscellaneous_2_description,

                    total_in_office,

                    str(request.tenant_id),
                    request.ob_store,
                    request.ob_date
                ))

                #
                # AUDITS
                #

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Petty Cash Advances",
                    old_petty_cash_advances,
                    request.ob_petty_cash_advances
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Currency In Safe",
                    old_currency_in_safe,
                    request.ob_currency_in_safe
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Coin In Safe",
                    old_coin_in_safe,
                    request.ob_coin_in_safe
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Currency In Office",
                    old_currency_in_office,
                    request.ob_currency_in_office
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Coin In Office",
                    old_coin_in_office,
                    request.ob_coin_in_office
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Checks",
                    old_checks,
                    request.ob_checks
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Returned Checks",
                    old_returned_checks,
                    request.ob_returned_checks
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Food Stamps",
                    old_food_stamps,
                    request.ob_food_stamps
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Bank Cards",
                    old_bank_cards,
                    request.ob_bank_cards
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Paid Outs CD",
                    old_paid_outs_cd,
                    request.ob_paid_outs_cd
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Employee Loans",
                    old_employee_loans,
                    request.ob_employee_loans
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Register Tills",
                    old_register_tills,
                    request.ob_register_tills
                )

                audit_if_changed(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "ATM Machine",
                    old_atm_machine,
                    request.ob_atm_machine
                )

                audit_if_changed_with_null_support(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Miscellaneous 1",
                    old_misc1,
                    request.ob_miscellaneous_1
                )

                audit_if_changed_with_null_support(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Miscellaneous 1 Description",
                    old_misc1_desc,
                    request.ob_miscellaneous_1_description
                )

                audit_if_changed_with_null_support(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Miscellaneous 2",
                    old_misc2,
                    request.ob_miscellaneous_2
                )

                audit_if_changed_with_null_support(
                    cur,
                    request.tenant_id,
                    request.ob_store,
                    request.ob_date,
                    request.user,
                    "Miscellaneous 2 Description",
                    old_misc2_desc,
                    request.ob_miscellaneous_2_description
                )

                conn.commit()

                return {
                    "return_value": 0,
                    "message": "Office Balance Updated Successfully"
                }

    except Exception as ex:

        if conn:
            conn.rollback()

        logger.exception(
            "Error in Form97 Update"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }