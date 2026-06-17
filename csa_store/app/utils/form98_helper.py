from datetime import datetime, timedelta

def sql_weekday(dt):
    """
    SQL Server style

    Sunday = 1
    Monday = 2
    ...
    Saturday = 7
    """

    return ((dt.weekday() + 1) % 7) + 1

def get_week_ending_date(cur, store):

    cur.execute("""
        SELECT sc_eow_last_run
        FROM retail_accounting.store_configuration
        WHERE sc_store = %s
    """, (store,))

    row = cur.fetchone()

    if not row:
        raise Exception("Week Ending Date not found")

    sc_eow_last_run = row[0]

    if sc_eow_last_run is None:
        raise Exception("Week Ending Date not found")

    compare_date = datetime.now()

    if sql_weekday(compare_date) == 1:

        return compare_date.date()

    if sc_eow_last_run.date() == compare_date.date():

        return (
            compare_date +
            timedelta(
                days=(8 - sql_weekday(compare_date))
            )
        ).date()

    return (
        sc_eow_last_run +
        timedelta(
            days=(8 - sql_weekday(sc_eow_last_run))
        )
    ).date()


def get_last_date_open(
        cur,
        store,
        week_ending_date):

    cur.execute("""
        SELECT sc_open_days
        FROM retail_accounting.store_configuration
        WHERE sc_store=%s
    """, (store,))

    row = cur.fetchone()

    if not row:
        raise Exception("Invalid Store")

    sc_open_days = row[0]

    last_date_open = week_ending_date

    if "1" not in sc_open_days:
        last_date_open = week_ending_date - timedelta(days=1)

    if "1" not in sc_open_days and "7" not in sc_open_days:
        last_date_open = week_ending_date - timedelta(days=2)

    if "1" not in sc_open_days and "7" not in sc_open_days and "6" not in sc_open_days:
        last_date_open = week_ending_date - timedelta(days=3)

    if "1" not in sc_open_days and "7" not in sc_open_days and "6" not in sc_open_days and "5" not in sc_open_days:
        last_date_open = week_ending_date - timedelta(days=4)

    if "1" not in sc_open_days and "7" not in sc_open_days and "6" not in sc_open_days and "5" not in sc_open_days and "4" not in sc_open_days:
        last_date_open = week_ending_date - timedelta(days=5)

    if "1" not in sc_open_days and "7" not in sc_open_days and "6" not in sc_open_days and "5" not in sc_open_days and "4" not in sc_open_days and "3" not in sc_open_days:
        last_date_open = week_ending_date - timedelta(days=6)

    return last_date_open


def update_dsc_with_form98(
        cur,
        store,
        week_ending_date):

    cur.execute("""
        SELECT
            sc_eod_last_run,
            sc_open_days
        FROM retail_accounting.store_configuration
        WHERE sc_store=%s
    """, (store,))

    row = cur.fetchone()

    if not row:
        raise Exception("Update DSC Total Failed")

    sc_eod_last_run = row[0]
    sc_open_days = row[1]

    last_date_open = get_last_date_open(
        cur,
        store,
        week_ending_date
    )

    if (
        ("1" in sc_open_days and sql_weekday(sc_eod_last_run) == 1)
        or
        ("1" not in sc_open_days and sql_weekday(sc_eod_last_run) == 7)
    ):

        cur.execute("""
            SELECT COALESCE(
                SUM(cb_cashier_over_short),
                0
            )
            FROM retail_history.cashier_balance
            WHERE cb_store=%s
            AND cb_date <= %s
        """,
        (
            store,
            week_ending_date
        ))

        work_amount = cur.fetchone()[0]

        cur.execute("""
            UPDATE retail.daily_sales_cash_total
            SET dsct_cashier_over_short=%s
            WHERE dsct_store=%s
            AND dsct_week_ending_date=%s
        """,
        (
            work_amount,
            store,
            week_ending_date
        ))

        cur.execute("""
            UPDATE retail.office_balance
            SET
                ob_cashier_over_short=0,
                ob_net_accountability=
                    ob_petty_cash_fund +
                    ob_petty_cash_advances
            WHERE ob_store=%s
            AND ob_date=%s
        """,
        (
            store,
            last_date_open
        ))


def update_wcb_with_form98(
        cur,
        store):

    week_ending_date = get_week_ending_date(
        cur,
        store
    )

    last_week_ending_date = (
        week_ending_date -
        timedelta(days=7)
    )

    cur.execute("""
        SELECT
            COALESCE(SUM(cb_sales),0),
            COALESCE(SUM(cb_voids),0),
            COALESCE(SUM(cb_returns),0),
            COALESCE(SUM(cb_checks),0),
            COALESCE(SUM(cb_gift_cards_tendered),0),
            COALESCE(SUM(cb_ebt),0),
            COALESCE(SUM(cb_credit_cards),0),
            COALESCE(SUM(cb_wic),0),
            COALESCE(SUM(cb_charges),0),
            COALESCE(SUM(cb_debit_cards),0),
            COALESCE(SUM(cb_vendor_coupons),0),
            COALESCE(SUM(cb_pfc_coupons),0),
            COALESCE(SUM(cb_cashier_over_short),0),
            COALESCE(SUM(cb_promo_coupons),0),
            COALESCE(SUM(cb_miscellaneous),0)
        FROM retail_history.cashier_balance
        WHERE cb_store=%s
        AND cb_date > %s
        AND cb_date <= %s
    """,
    (
        store,
        last_week_ending_date,
        week_ending_date
    ))

    totals = cur.fetchone()

    cur.execute("""
        UPDATE retail.wtd_cashier_balance
        SET
            wcb_sales=%s,
            wcb_voids=%s,
            wcb_returns=%s,
            wcb_checks=%s,
            wcb_gift_cards_tendered=%s,
            wcb_ebt=%s,
            wcb_credit_cards=%s,
            wcb_wic=%s,
            wcb_charges=%s,
            wcb_debit_cards=%s,
            wcb_vendor_coupons=%s,
            wcb_pfc_coupons=%s,
            wcb_cashier_over_short=%s,
            wcb_promo_coupons=%s,
            wcb_miscellaneous=%s
        WHERE wcb_store=%s
        AND wcb_week_ending_date=%s
    """,
    (
        *totals,
        store,
        week_ending_date
    ))


def insert_cashier_balance(
        cur,
        tenant_id,
        request):

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
            cb_miscellaneous,
            created_by,
            last_updated_by
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """,
    (
        tenant_id,
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
        request.cb_miscellaneous,
        request.cb_user,
        request.cb_user
    ))


def insert_audit(
        cur,
        tenant_id,
        request):

    comment = (
        f"Employee ID - "
        f"{request.cb_employee_id} "
        f"Till - "
        f"{request.cb_till}"
    )

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
            8,
            'I',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        tenant_id,
        request.cb_store,
        request.cb_date,
        request.cb_user,
        comment
    ))


def insert_delete_audit(
        cur,
        tenant_id,
        request):

    comment = (
        f"Employee ID - "
        f"{request.cb_employee_id} "
        f"Till - "
        f"{request.cb_till}"
    )

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
            8,
            'D',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        tenant_id,
        request.cb_store,
        request.cb_date,
        request.cb_user,
        comment
    ))


