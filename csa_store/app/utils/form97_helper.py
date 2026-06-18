import logging

from datetime import timedelta

logger = logging.getLogger(__name__)


def get_week_ending_date(
        cur,
        tenant_id,
        store):
    """
    Equivalent of:

    csa_WeekEndingDate
    """

    cur.execute("""
        SELECT
            sc_eow_last_run
        FROM retail_accounting.store_configuration
        WHERE tenant_id=%s
        AND sc_store=%s
    """,
    (
        str(tenant_id),
        store
    ))

    row = cur.fetchone()

    if not row:

        raise Exception(
            "Week Ending Date not found"
        )

    sc_eow_last_run = row[0]

    compare_date = sc_eow_last_run.date()

    if compare_date.weekday() == 6:

        return compare_date

    return (
        sc_eow_last_run +
        timedelta(
            days=(
                6 -
                sc_eow_last_run.weekday()
            )
        )
    ).date()


def insert_form97_audit(
        cur,
        tenant_id,
        store,
        business_date,
        user,
        comment):
    """
    Insert audit row.
    Equivalent of retail_history.audit insert.
    """

    cur.execute("""
        INSERT INTO retail_history.audit
        (
            tenant_id,
            a_store,
            a_date,
            a_form_type,
            a_action,
            a_creation_date,
            a_user,
            a_comment
        )
        VALUES
        (
            %s,
            %s,
            %s,
            15,
            'U',
            NOW(),
            %s,
            %s
        )
    """,
    (
        str(tenant_id),
        store,
        business_date,
        user,
        comment
    ))


def audit_if_changed(
        cur,
        tenant_id,
        store,
        business_date,
        user,
        field_name,
        old_value,
        new_value):
    """
    Standard audit helper.
    """

    if old_value != new_value:

        insert_form97_audit(
            cur,
            tenant_id,
            store,
            business_date,
            user,
            (
                f"{field_name} Changed From: "
                f"{old_value} To: {new_value}"
            )
        )


def audit_if_changed_with_null_support(
        cur,
        tenant_id,
        store,
        business_date,
        user,
        field_name,
        old_value,
        new_value):
    """
    SQL replica for Miscellaneous fields.
    Handles:

    Changed From: Nothing To: XXX
    """

    if old_value != new_value:

        if old_value is None:

            comment = (
                f"{field_name} Changed From: "
                f"Nothing To: {new_value}"
            )

        else:

            comment = (
                f"{field_name} Changed From: "
                f"{old_value} To: {new_value}"
            )

        insert_form97_audit(
            cur,
            tenant_id,
            store,
            business_date,
            user,
            comment
        )


def calculate_net_accountability(
        petty_cash_fund,
        petty_cash_advances,
        cashier_over_short):
    """
    SQL Replica

    OB_Net_Accountability =
        OB_Petty_Cash_Fund +
        OB_Petty_Cash_Advances +
        OB_Cashier_Over_Short
    """

    return (
        petty_cash_fund +
        petty_cash_advances +
        cashier_over_short
    )


def calculate_total_in_office(
        currency_in_safe,
        coin_in_safe,
        currency_in_office,
        coin_in_office,
        checks,
        returned_checks,
        food_stamps,
        bank_cards,
        paid_outs_cd,
        employee_loans,
        register_tills,
        atm_machine,
        miscellaneous_1,
        miscellaneous_2):
    """
    SQL Replica

    OB_Total_In_Office =
        Currency_In_Safe +
        Coin_In_Safe +
        Currency_In_Office +
        Coin_In_Office +
        Checks +
        Returned_Checks +
        Food_Stamps +
        Bank_Cards +
        Paid_Outs_CD +
        Employee_Loans +
        Register_Tills +
        ATM_Machine +
        Miscellaneous_1 +
        Miscellaneous_2
    """

    return (
        currency_in_safe +
        coin_in_safe +
        currency_in_office +
        coin_in_office +
        checks +
        returned_checks +
        food_stamps +
        bank_cards +
        paid_outs_cd +
        employee_loans +
        register_tills +
        atm_machine +
        miscellaneous_1 +
        miscellaneous_2
    )