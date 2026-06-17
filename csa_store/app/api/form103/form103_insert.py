import logging

from datetime import timedelta

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.form103.form103_insert_request import (
    Form103InsertRequest
)

from app.utils.form98_helper import (
    get_week_ending_date
)

from app.utils.form103_helper import (
    update_dsc_with_form103
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form103",
    tags=["Form103"]
)


@router.post("/insert")
def form103_insert(
        request: Form103InsertRequest):
    """
    Equivalent of:

    csa_Form103_Insert
    """

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                # --------------------------------------------------
                # Store Validation
                # --------------------------------------------------

                if not request.def_store:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                # --------------------------------------------------
                # Week Ending Date
                # --------------------------------------------------

                week_ending_date = get_week_ending_date(
                    cur,
                    request.def_store
                )

                last_week_ending_date = (
                    week_ending_date -
                    timedelta(days=7)
                )

                # --------------------------------------------------
                # Date Validation
                # --------------------------------------------------

                if (
                    request.def_date <= last_week_ending_date
                    or
                    request.def_date >
                    (week_ending_date + timedelta(days=1))
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }

                # --------------------------------------------------
                # Form Type Validation
                # --------------------------------------------------

                if request.def_form_type != 2:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Form Type"
                    }

                # --------------------------------------------------
                # Department Validation
                # --------------------------------------------------

                if not request.def_department:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Department"
                    }

                # --------------------------------------------------
                # User Validation
                # --------------------------------------------------

                if (
                    request.def_user is None
                    or
                    request.def_user.strip() == ""
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid User"
                    }

                # --------------------------------------------------
                # Vendor / Item Validation
                # --------------------------------------------------

                if (
                    request.def_descriptor_1 is None
                    or
                    request.def_descriptor_1.strip() == ""
                ):

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Vendor/Item"
                    }

                # --------------------------------------------------
                # Cost Validation
                # --------------------------------------------------

                if request.def_amount_1 is None:

                    return {
                        "return_value": 1,
                        "error_message": "Invalid Cost"
                    }

                # --------------------------------------------------
                # Department Description
                # --------------------------------------------------

                cur.execute("""
                    SELECT d_description
                    FROM retail_accounting.departments
                    WHERE d_id=%s
                """,
                (
                    request.def_department,
                ))

                department_row = cur.fetchone()

                if not department_row:

                    return {
                        "return_value": 1,
                        "error_message": "Department Not Found"
                    }

                department_description = (
                    department_row[0]
                )

                # --------------------------------------------------
                # Insert DEF
                # --------------------------------------------------

                cur.execute("""
                    INSERT INTO
                    retail_accounting.data_entry_forms
                    (
                        tenant_id,
                        def_store,
                        def_date,
                        def_form_type,
                        def_department,
                        def_user,
                        def_descriptor_1,
                        def_amount_1,
                        def_amount_2,
                        def_retail_acct_update_flag,
                        created_by,
                        updated_by
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
                        0,
                        'N',
                        %s,
                        %s
                    )
                    RETURNING def_id
                """,
                (
                    str(request.tenant_id),
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_department,
                    request.def_user,
                    request.def_descriptor_1,
                    request.def_amount_1,
                    request.def_user,
                    request.def_user
                ))

                def_id = cur.fetchone()[0]

                # --------------------------------------------------
                # Update DSC
                # --------------------------------------------------

                update_dsc_with_form103(
                    cur,
                    request.def_store,
                    request.def_department,
                    week_ending_date
                )

                # --------------------------------------------------
                # Commit
                # --------------------------------------------------

                conn.commit()

                # --------------------------------------------------
                # Audit
                # --------------------------------------------------

                comment = (
                    f"Department - "
                    f"{department_description}, "
                    f"Amount - "
                    f"{request.def_amount_1}, "
                    f"Identity - "
                    f"{def_id}"
                )

                cur.execute("""
                    INSERT INTO
                    retail_history.audit
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
                        103,
                        'I',
                        CURRENT_TIMESTAMP,
                        %s,
                        %s
                    )
                """,
                (
                    str(request.tenant_id),
                    request.def_store,
                    request.def_date,
                    request.def_user,
                    comment
                ))

                conn.commit()

                return {
                    "return_value": 0,
                    "error_message": "",
                    "def_id": def_id
                }

    except Exception as ex:

        logger.exception(
            "Error in Form103 Insert"
        )

        try:
            conn.rollback()
        except:
            pass

        return {
            "return_value": 1,
            "error_message": str(ex)
        }


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