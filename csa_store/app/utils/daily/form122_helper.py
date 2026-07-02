def update_form111_with_postage_stamps(
        cur,
        store,
        psi_date,
        week_ending_date):
    """
    Equivalent:
    csa_UpdateForm111WithPostageStamps
    """

    cur.execute("""
        SELECT COUNT(*)
        FROM retail_accounting.data_entry_forms
        WHERE def_store=%s
        AND def_date=%s
        AND def_form_type=7
        AND def_user='PostageStampInventory'
    """,
    (
        store,
        week_ending_date
    ))

    count = cur.fetchone()[0]

    if count == 0:

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
                def_amount_1,
                def_amount_2,
                def_retail_acct_update_flag
            )
            SELECT
                psi.tenant_id,
                psi.psi_store,
                %s,
                7,
                NULL,
                'PostageStampInventory',
                'Postage Stamp Inventory',
                CONCAT('WEEK-TO-DATE: ', psi.psi_books_sold),
                0,
                (sc.sc_postage_stamp_fee * psi.psi_books_sold),
                'N'
            FROM retail_history.postage_stamp_inventory psi
            INNER JOIN retail_accounting.store_configuration sc
                ON psi.psi_store=sc.sc_store
            WHERE psi.psi_store=%s
            AND psi.psi_date=%s
        """,
        (
            week_ending_date,
            store,
            psi_date
        ))

    else:

        cur.execute("""
            UPDATE retail_accounting.data_entry_forms def
            SET
                def_descriptor_2 =
                    CONCAT('WEEK-TO-DATE: ', src.books_sold),
                def_amount_2 =
                    sc.sc_postage_stamp_fee * src.books_sold
            FROM
            (
                SELECT
                    psi_store,
                    SUM(psi_books_sold) books_sold
                FROM retail_history.postage_stamp_inventory
                WHERE psi_store=%s
                AND psi_date<=%s
                GROUP BY psi_store
            ) src
            INNER JOIN retail_accounting.store_configuration sc
                ON src.psi_store=sc.sc_store
            WHERE def.def_store=src.psi_store
            AND def.def_form_type=7
            AND def.def_user='PostageStampInventory'
            AND def.def_date=%s
        """,
        (
            store,
            week_ending_date,
            week_ending_date
        ))



def update_dsc_with_form111(
        cur,
        store,
        week_ending_date):
    """
    Equivalent:
    csa_UpdateDSCWithForm111
    """

    cur.execute("""
        SELECT
            COALESCE(
                SUM(def_amount_2),
                0
            )
        FROM retail_accounting.data_entry_forms
        WHERE def_store=%s
        AND def_form_type=7
        AND def_date<=%s
    """,
    (
        store,
        week_ending_date
    ))

    work_amount = cur.fetchone()[0]

    cur.execute("""
        UPDATE retail_accounting.wtd_net_receipts
        SET wnr_form111_total=%s
        WHERE wnr_store=%s
        AND wnr_week_ending_date=%s
    """,
    (
        work_amount,
        store,
        week_ending_date
    ))

    cur.execute("""
        UPDATE retail.daily_sales_cash_total dsct
        SET dsct_net_receipts =
            wnr.wnr_form111_total +
            wnr.wnr_ar_collected
        FROM retail_accounting.wtd_net_receipts wnr
        WHERE dsct.dsct_store=wnr.wnr_store
        AND dsct.dsct_week_ending_date=
            wnr.wnr_week_ending_date
        AND dsct.dsct_store=%s
        AND dsct.dsct_week_ending_date=%s
    """,
    (
        store,
        week_ending_date
    ))



def insert_form122_audit(
        cur,
        tenant_id,
        store,
        psi_date,
        user,
        comment):
    """
    Insert Form122 Audit
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
            10,
            'U',
            CURRENT_TIMESTAMP,
            %s,
            %s
        )
    """,
    (
        str(tenant_id),
        store,
        psi_date,
        user,
        comment
    ))