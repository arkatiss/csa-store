import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def check_wtd_net_sales_exists(
    cur,
    tenant_id,
    store,
    week_ending_date
):
    """
    Check whether the WTD Net Sales record exists.
    """

    cur.execute(
        """
        SELECT COUNT(*)
        FROM retail_accounting.wtd_net_sales
        WHERE
            tenant_id = %s
        AND
            wns_store = %s
        AND
            wns_week_ending_date = %s
        """,
        (
            str(tenant_id),
            store,
            week_ending_date,
        ),
    )

    return cur.fetchone()[0] > 0


def update_daily_sales_cash_total(
    cur,
    tenant_id,
    store,
    week_ending_date
):
    """
    Equivalent of:

    Update retail_accounting.daily_sales_cash_total
    Set DSCT_Net_Sales_Amount =
    (
        WNS_Gross_Receipts -
        WNS_Voids -
        WNS_Refunds -
        WNS_Tax_Credits -
        WNS_Deposit_Cancels -
        WNS_Bottle_Returns -
        WNS_Store_Coupons
    ) +
    WNS_Other_Sales
    """

    cur.execute(
        """
        UPDATE retail_accounting.daily_sales_cash_total dsct
        SET
            dsct_net_sales_amount =
            (
                wns.wns_gross_receipts
                - wns.wns_voids
                - wns.wns_refunds
                - wns.wns_tax_credits
                - wns.wns_deposit_cancels
                - wns.wns_bottle_returns
                - wns.wns_store_coupons
                + wns.wns_other_sales
            )
        FROM retail_accounting.wtd_net_sales wns
        WHERE
            dsct.tenant_id = wns.tenant_id
        AND
            dsct.dsct_store = wns.wns_store
        AND
            dsct.dsct_week_ending_date = wns.wns_week_ending_date
        AND
            dsct.tenant_id = %s
        AND
            dsct.dsct_store = %s
        AND
            dsct.dsct_week_ending_date = %s
        """,
        (
            str(tenant_id),
            store,
            week_ending_date,
        ),
    )


def insert_audit_record(
    cur,
    tenant_id,
    store,
    week_ending_date,
    user,
    comment,
):
    """
    Insert Audit Record
    """

    cur.execute(
        """
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
            11,
            'U',
            NOW(),
            %s,
            %s
        )
        """,
        (
            str(tenant_id),
            store,
            week_ending_date,
            user,
            comment,
        ),
    )