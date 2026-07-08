import logging

logger = logging.getLogger(__name__)


def get_department_description(cur, department_id: int):
    """
    Equivalent SQL:

    Select @D_Description = D_Description
    From retail_accounting.departments
    Where D_ID = @WGI_Department
    """

    cur.execute(
        """
        SELECT d_description
        FROM retail_accounting.departments
        WHERE d_id = %s
        """,
        (department_id,)
    )

    row = cur.fetchone()

    if row:
        return row[0]

    return ""


def insert_audit_record(
    cur,
    tenant_id,
    store,
    week_ending_date,
    user,
    comment
):
    """
    Equivalent SQL:

    Insert Into retail_history.audit
    Values
    (
        @Store,
        @Week_Ending_Date,
        22,
        'U',
        GETDATE(),
        @User,
        @Comment
    )
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
            %s,
            %s,
            NOW(),
            %s,
            %s
        )
        """,
        (
            str(tenant_id),
            store,
            week_ending_date,
            22,
            "U",
            user,
            comment
        )
    )