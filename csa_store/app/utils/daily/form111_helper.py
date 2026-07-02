import logging

logger = logging.getLogger(__name__)


def update_dsc_with_form111(
        cur,
        tenant_id,
        store,
        week_ending_date):
    """
    Equivalent of:

    csa_UpdateDSCWithForm111
    """

    #
    # FORM111 TOTAL
    #

    cur.execute("""
        SELECT
            COALESCE(
                SUM(def_amount_2),
                0
            )
        FROM retail_accounting.data_entry_forms
        WHERE tenant_id=%s
        AND def_store=%s
        AND def_form_type=7
        AND def_date<=%s
    """,
    (
        str(tenant_id),
        store,
        week_ending_date
    ))

    work_amount = cur.fetchone()[0]

    #
    # UPDATE WTD NET RECEIPTS
    #

    cur.execute("""
        UPDATE retail_accounting.wtd_net_receipts
        SET wnr_form111_total=%s
        WHERE tenant_id=%s
        AND wnr_store=%s
        AND wnr_week_ending_date=%s
    """,
    (
        work_amount,
        str(tenant_id),
        store,
        week_ending_date
    ))

    #
    # UPDATE DAILY SALES CASH TOTAL
    #

    cur.execute("""
        UPDATE retail_accounting.daily_sales_cash_total dsct
        SET dsct_net_receipts=
            wnr.wnr_form111_total +
            wnr.wnr_ar_collected
        FROM retail_accounting.wtd_net_receipts wnr
        WHERE dsct.tenant_id=%s
        AND wnr.tenant_id=%s
        AND dsct.dsct_store=wnr.wnr_store
        AND dsct.dsct_week_ending_date=
            wnr.wnr_week_ending_date
        AND dsct.dsct_store=%s
        AND dsct.dsct_week_ending_date=%s
    """,
    (
        str(tenant_id),
        str(tenant_id),
        store,
        week_ending_date
    ))



def insert_form111_insert_audit(
        cur,
        tenant_id,
        store,
        form_date,
        form_type,
        user,
        amount,
        def_id):
    """
    Insert Form111 audit record.
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
            'I',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        str(tenant_id),
        store,
        form_date,
        form_type,
        user,
        f"Amount - {amount}, Identity - {def_id}"
    ))


def insert_form111_update_audit(
        cur,
        tenant_id,
        store,
        form_date,
        form_type,
        user,
        comment):
    """
    Insert Form111 update audit.
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
        form_date,
        form_type,
        user,
        comment
    ))


def insert_form111_delete_audit(
        cur,
        tenant_id,
        store,
        form_date,
        form_type,
        user,
        amount,
        def_id):
    """
    Insert Form111 delete audit.
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
            'D',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        str(tenant_id),
        store,
        form_date,
        form_type,
        user,
        f"Amount - {amount}, Identity - {def_id}"
    ))