from datetime import date, timedelta


def get_sql_weekday(dt: date) -> int:
    """
    Returns SQL Server style weekday.

    SQL Server:
        Sunday    = 1
        Monday    = 2
        Tuesday   = 3
        Wednesday = 4
        Thursday  = 5
        Friday    = 6
        Saturday  = 7
    """
    return (dt.isoweekday() % 7) + 1


def get_week_ending_date(sc_eow_last_run: date) -> date:
    """
    Equivalent to SQL:

    IF DATEPART(WEEKDAY,@SC_EOW_LAST_RUN)=1
        WeekEndingDate = SC_EOW_LAST_RUN
    ELSE
        WeekEndingDate =
            DATEADD(DAY,
                    (8-DATEPART(WEEKDAY,@SC_EOW_LAST_RUN)),
                    @SC_EOW_LAST_RUN)
    """

    weekday = get_sql_weekday(sc_eow_last_run)

    if weekday == 1:
        return sc_eow_last_run

    return sc_eow_last_run + timedelta(days=(8 - weekday))


def is_valid_date(def_date: date, week_ending_date: date) -> bool:
    """
    Equivalent to SQL:

    IF @DEF_Date < DATEADD(DAY,-7,@WeekEndingDate)
       OR
       @DEF_Date > DATEADD(DAY,1,@WeekEndingDate)

    Valid Range:
        WeekEndingDate - 7
        through
        WeekEndingDate + 1
    """

    start_date = week_ending_date - timedelta(days=7)
    end_date = week_ending_date + timedelta(days=1)

    return start_date <= def_date <= end_date

def insert_form106_audit(
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
    csa_Form106_Insert Audit
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

def update_form106_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        comment):
    """
    Equivalent of
    csa_Form106_Update Audit
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

def delete_form106_audit(
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
    csa_Form106_Delete Audit
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

def form106_update_audit(
        cur,
        tenant_id,
        store,
        date_value,
        form_type,
        user,
        old_record,
        new_record,
        old_department_description,
        new_department_description):
    """
    Equivalent of SQL
    csa_Form106_Update Audit
    """

    # Audit date change
    if old_record["date"].date() != new_record["date"].date():

        comment = (
            f"Date Changed From: "
            f"{old_record['date'].strftime('%m/%d/%y')} "
            f"To: "
            f"{new_record['date'].strftime('%m/%d/%y')}"
        )

        update_form106_audit(
            cur,
            tenant_id,
            store,
            date_value,
            form_type,
            user,
            comment
        )

    # Audit department change
    if old_record["department"] != new_record["department"]:

        comment = (
            f"Department Changed From: "
            f"{old_department_description} "
            f"To: "
            f"{new_department_description}"
        )

        update_form106_audit(
            cur,
            tenant_id,
            store,
            date_value,
            form_type,
            user,
            comment
        )

    # Audit user change
    if old_record["user"] != new_record["user"]:

        comment = (
            f"User Changed From: "
            f"{old_record['user']} "
            f"To: "
            f"{new_record['user']}"
        )

        update_form106_audit(
            cur,
            tenant_id,
            store,
            date_value,
            form_type,
            user,
            comment
        )

    # Audit descriptor 1 change
    if old_record["descriptor_1"] != new_record["descriptor_1"]:

        comment = (
            f"Descriptor 1 Changed From: "
            f"{old_record['descriptor_1']} "
            f"To: "
            f"{new_record['descriptor_1']}"
        )

        update_form106_audit(
            cur,
            tenant_id,
            store,
            date_value,
            form_type,
            user,
            comment
        )

    # Audit descriptor 2 change
    if old_record["descriptor_2"] != new_record["descriptor_2"]:

        if old_record["descriptor_2"] is None:

            comment = (
                f"Descriptor 2 Changed From: "
                f"Blank "
                f"To: "
                f"{new_record['descriptor_2']}"
            )

        else:

            comment = (
                f"Descriptor 2 Changed From: "
                f"{old_record['descriptor_2']} "
                f"To: "
                f"{new_record['descriptor_2']}"
            )

        update_form106_audit(
            cur,
            tenant_id,
            store,
            date_value,
            form_type,
            user,
            comment
        )

    # Audit amount change
    if old_record["amount"] != new_record["amount"]:

        comment = (
            f"Amount 2 Changed From: "
            f"{old_record['amount']:.2f} "
            f"To: "
            f"{new_record['amount']:.2f}"
        )

        update_form106_audit(
            cur,
            tenant_id,
            store,
            date_value,
            form_type,
            user,
            comment
        )