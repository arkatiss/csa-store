import logging

logger = logging.getLogger(__name__)


def update_dsc_with_form105a(
        cur,
        store,
        week_ending_date):
    """
    Equivalent of:

    csa_UpdateDSCWithForm105a
    """

    #
    # Accounts Receivable Collected
    #

    cur.execute("""
        SELECT
            COALESCE(
                SUM(def_amount_2),
                0
            )
        FROM retail_accounting.data_entry_forms
        WHERE def_store=%s
        AND def_form_type=4
        AND def_date <= %s
    """,
    (
        store,
        week_ending_date
    ))

    work_amount = cur.fetchone()[0]

    #
    # Update WTD Net Receipts
    #

    cur.execute("""
        UPDATE retail_accounting.wtd_net_receipts
        SET wnr_ar_collected=%s
        WHERE wnr_store=%s
        AND wnr_week_ending_date=%s
    """,
    (
        work_amount,
        store,
        week_ending_date
    ))

    #
    # Update Daily Sales Cash Total
    #

    cur.execute("""
        UPDATE retail.daily_sales_cash_total dsct
        SET dsct_net_receipts =
            COALESCE(wnr.wnr_form111_total,0)
            +
            COALESCE(wnr.wnr_ar_collected,0)
        FROM retail_accounting.wtd_net_receipts wnr
        WHERE dsct.dsct_store = wnr.wnr_store
        AND dsct.dsct_week_ending_date =
            wnr.wnr_week_ending_date
        AND dsct.dsct_store=%s
        AND dsct.dsct_week_ending_date=%s
    """,
    (
        store,
        week_ending_date
    ))


def insert_form105a_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        amount,
        identity):
    """
    Insert Form105A Audit
    """

    comment = (
        f"Amount - {amount}, "
        f"Identity - {identity}"
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
            %s,
            'I',
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


def insert_form105a_update_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        comment):
    """
    Insert Form105A Update Audit
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