def update_dsc_with_form104(
        cur,
        store,
        week_ending_date):
    """
    Equivalent of:
    csa_UpdateDSCWithForm104
    """

    cur.execute("""
        SELECT
            COALESCE(
                SUM(def_amount_2),
                0
            )
        FROM retail_accounting.data_entry_forms
        WHERE def_store=%s
        AND def_date <= %s
        AND def_form_type=3
    """,
    (
        store,
        week_ending_date
    ))

    work_amount = cur.fetchone()[0]

    cur.execute("""
        UPDATE retail.daily_sales_cash_total
        SET dsct_cash_expense=%s
        WHERE dsct_store=%s
        AND dsct_week_ending_date=%s
    """,
    (
        work_amount,
        store,
        week_ending_date
    ))


def insert_form104_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        department_description,
        amount,
        identity):
    """
    Insert Form104 Audit
    """

    comment = (
        f"Department - "
        f"{department_description}, "
        f"Amount - "
        f"{amount}, "
        f"Identity - "
        f"{identity}"
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


def insert_form104_update_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        comment):
    """
    Form104 Update Audit
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


def insert_form104_delete_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        department_description,
        amount,
        identity):
    """
    Equivalent of
    csa_Form104_Delete Audit
    """

    comment = (
        f"Department - "
        f"{department_description}, "
        f"Amount - "
        f"{amount}, "
        f"Identity - "
        f"{identity}"
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