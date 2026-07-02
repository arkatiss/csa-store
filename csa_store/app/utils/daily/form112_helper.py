import logging

logger = logging.getLogger(__name__)

def update_form111_with_drink_machine_sales(
        cur,
        tenant_id,
        store,
        dms_date,
        machine_nbr,
        week_ending_date):
    """
    Equivalent of:

    csa_UpdateForm111WithDrinkMachineSales
    """

    #
    # CHECK IF FORM111 RECORDS EXIST
    #

    cur.execute("""
        SELECT COUNT(*)
        FROM retail_accounting.data_entry_forms
        WHERE tenant_id=%s
        AND def_store=%s
        AND def_date=%s
        AND def_form_type=7
        AND def_user='DrinkMachineSales'
    """,
    (
        str(tenant_id),
        store,
        week_ending_date
    ))

    count = cur.fetchone()[0]

    #
    # INSERT
    #

    if count == 0:

        #
        # DrinkMachineSales
        #

        cur.execute("""
            INSERT INTO retail_accounting.data_entry_forms
            (
                tenant_id,
                def_store,
                def_date,
                def_form_type,
                def_department,
                def_user,
                def_descriptor_1,
                def_descriptor_2,
                def_descriptor_3,
                def_descriptor_4,
                def_amount_1,
                def_amount_2,
                def_retail_acct_update_flag
            )
            SELECT
                %s,
                q.dms_store,
                %s,
                7,
                NULL,
                'DrinkMachineSales',
                'Drink Machine Sales',
                NULL,
                NULL,
                NULL,
                0,
                ROUND(
                    (
                        q.dms_actual_sales /
                        (1 + sc.sc_tax_rate_1)
                    )::numeric,
                    2
                ),
                'N'
            FROM
            (
                SELECT
                    dms_store,
                    dms_actual_sales
                FROM retail_history.drink_machine_sales
                WHERE tenant_id=%s
                AND dms_store=%s
                AND dms_date=%s
                AND dms_machine_nbr=%s
            ) q
            INNER JOIN retail_accounting.store_configuration sc
                ON q.dms_store=sc.sc_store
                AND sc.tenant_id=%s
        """,
        (
            str(tenant_id),
            week_ending_date,
            str(tenant_id),
            store,
            dms_date,
            machine_nbr,
            str(tenant_id)
        ))

        #
        # TaxOnDrinkSales
        #

        cur.execute("""
            INSERT INTO retail_accounting.data_entry_forms
            (
                tenant_id,
                def_store,
                def_date,
                def_form_type,
                def_department,
                def_user,
                def_descriptor_1,
                def_descriptor_2,
                def_descriptor_3,
                def_descriptor_4,
                def_amount_1,
                def_amount_2,
                def_retail_acct_update_flag
            )
            SELECT
                %s,
                q.dms_store,
                %s,
                7,
                NULL,
                'TaxOnDrinkSales',
                'Tax On Drink Sales',
                NULL,
                NULL,
                NULL,
                0,
                q.dms_actual_sales -
                ROUND(
                    (
                        q.dms_actual_sales /
                        (1 + sc.sc_tax_rate_1)
                    )::numeric,
                    2
                ),
                'N'
            FROM
            (
                SELECT
                    dms_store,
                    dms_actual_sales
                FROM retail_history.drink_machine_sales
                WHERE tenant_id=%s
                AND dms_store=%s
                AND dms_date=%s
                AND dms_machine_nbr=%s
            ) q
            INNER JOIN retail_accounting.store_configuration sc
                ON q.dms_store=sc.sc_store
                AND sc.tenant_id=%s
        """,
        (
            str(tenant_id),
            week_ending_date,
            str(tenant_id),
            store,
            dms_date,
            machine_nbr,
            str(tenant_id)
        ))

    #
    # UPDATE
    #

    else:

        cur.execute("""
            SELECT
                COALESCE(
                    SUM(dms_actual_sales),
                    0
                )
            FROM retail_history.drink_machine_sales
            WHERE tenant_id=%s
            AND dms_store=%s
            AND dms_date<=%s
        """,
        (
            str(tenant_id),
            store,
            week_ending_date
        ))

        actual_sales = cur.fetchone()[0]

        cur.execute("""
            SELECT
                sc_tax_rate_1
            FROM retail_accounting.store_configuration
            WHERE tenant_id=%s
            AND sc_store=%s
        """,
        (
            str(tenant_id),
            store
        ))

        tax_rate = cur.fetchone()[0]

        drink_sales_amount = round(
            float(actual_sales) /
            (1 + float(tax_rate)),
            2
        )

        tax_amount = (
            float(actual_sales) -
            drink_sales_amount
        )

        #
        # DrinkMachineSales
        #

        cur.execute("""
            UPDATE retail_accounting.data_entry_forms
            SET def_amount_2=%s
            WHERE tenant_id=%s
            AND def_store=%s
            AND def_date=%s
            AND def_form_type=7
            AND def_user='DrinkMachineSales'
        """,
        (
            drink_sales_amount,
            str(tenant_id),
            store,
            week_ending_date
        ))

        #
        # TaxOnDrinkSales
        #

        cur.execute("""
            UPDATE retail_accounting.data_entry_forms
            SET def_amount_2=%s
            WHERE tenant_id=%s
            AND def_store=%s
            AND def_date=%s
            AND def_form_type=7
            AND def_user='TaxOnDrinkSales'
        """,
        (
            tax_amount,
            str(tenant_id),
            store,
            week_ending_date
        ))


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
        UPDATE retail.daily_sales_cash_total dsct
        SET dsct_net_receipts =
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