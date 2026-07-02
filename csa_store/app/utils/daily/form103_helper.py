import logging

from app.utils.daily.form98_helper import (
    get_week_ending_date
)

logger = logging.getLogger(__name__)


DEPARTMENT_MAPPING = {
    1: "wdp_grocery",
    2: "wdp_meat",
    3: "wdp_produce",
    4: "wdp_ff_dairy",
    5: "wdp_deli_bakery",
    6: "wdp_pharmacy",
    7: "wdp_florist",
    8: "wdp_seafood",
    9: "wdp_hba",
    10: "wdp_sushi",
    11: "wdp_fuel",
    12: "wdp_starbucks",
    13: "wdp_miscellaneous",
    14: "wdp_kitchen_ware",
    15: "wdp_dream_dinners",
    16: "wdp_other",
    18: "wdp_restaurant",
    19: "wdp_fuel_grocery",
    20: "wdp_floral_independent",
    21: "wdp_post_office",
    22: "wdp_fuel_independent"
}


def update_dsc_with_form103(
        cur,
        store,
        department,
        week_ending_date):
    """
    Equivalent of:
    csa_UpdateDSCWithForm103
    """

    if department not in DEPARTMENT_MAPPING:
        raise Exception("Invalid Department")

    column_name = DEPARTMENT_MAPPING[department]

    cur.execute("""
        SELECT COALESCE(
            SUM(def_amount_2),
            0
        )
        FROM retail_accounting.data_entry_forms
        WHERE def_store=%s
        AND def_form_type=2
        AND def_department=%s
        AND def_date <= %s
    """,
    (
        store,
        department,
        week_ending_date
    ))

    work_amount = cur.fetchone()[0]

    cur.execute(f"""
        UPDATE retail_accounting.wtd_department_pay_outs
        SET {column_name}=%s
        WHERE wdp_store=%s
        AND wdp_week_ending_date=%s
    """,
    (
        work_amount,
        store,
        week_ending_date
    ))

    cur.execute("""
        UPDATE retail_accounting.daily_sales_cash_total
        SET dsct_dept_payouts =
            (
                SELECT
                    COALESCE(wdp_grocery,0) +
                    COALESCE(wdp_meat,0) +
                    COALESCE(wdp_produce,0) +
                    COALESCE(wdp_ff_dairy,0) +
                    COALESCE(wdp_deli_bakery,0) +
                    COALESCE(wdp_pharmacy,0) +
                    COALESCE(wdp_florist,0) +
                    COALESCE(wdp_seafood,0) +
                    COALESCE(wdp_hba,0) +
                    COALESCE(wdp_sushi,0) +
                    COALESCE(wdp_fuel,0) +
                    COALESCE(wdp_starbucks,0) +
                    COALESCE(wdp_miscellaneous,0) +
                    COALESCE(wdp_kitchen_ware,0) +
                    COALESCE(wdp_dream_dinners,0) +
                    COALESCE(wdp_other,0) +
                    COALESCE(wdp_restaurant,0) +
                    COALESCE(wdp_fuel_grocery,0) +
                    COALESCE(wdp_floral_independent,0) +
                    COALESCE(wdp_post_office,0) +
                    COALESCE(wdp_fuel_independent,0)
                FROM retail_accounting.wtd_department_pay_outs
                WHERE wdp_store=%s
                AND wdp_week_ending_date=%s
            )
        WHERE dsct_store=%s
        AND dsct_week_ending_date=%s
    """,
    (
        store,
        week_ending_date,
        store,
        week_ending_date
    ))


def insert_form103_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        comment):

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
            %s,
            'U',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        str(tenant_id),
        store,
        date_value,
        form_type,
        user,
        comment
    ))


def insert_form103_delete_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        comment):

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
            %s,
            'D',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        str(tenant_id),
        store,
        date_value,
        form_type,
        user,
        comment
    ))