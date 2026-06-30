# form106_insert.py

import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.form106.form106_insert_schema import Form106InsertRequest
from app.utils.form106_helper import get_week_ending_date, is_valid_date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/form106", tags=["Form106"])


@router.post("/insert")
def csa_form106_insert(request: Form106InsertRequest):
    conn = None

    try:

        if request.def_store is None or str(request.def_store).strip() == "":
            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        with DBConnection() as conn:
            with conn.cursor() as cur:

 
                cur.execute("""
                    SELECT sc_eow_last_run
                    FROM retail_accounting.store_configuration
                    WHERE sc_store = %s
                """, (
                    request.def_store,
                ))

                row = cur.fetchone()

                if not row:
                    return {
                        "return_value": 1,
                        "error_message": "Store Configuration Not Found"
                    }

                sc_eow_last_run = row[0]

                if sc_eow_last_run is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Store"
                    }

                sc_eow_last_run = sc_eow_last_run.date()


                week_ending_date = get_week_ending_date(sc_eow_last_run)

  
                if not is_valid_date(request.def_date, week_ending_date):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Date"
                    }


                if request.def_form_type != 6:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Form Type"
                    }

                if request.def_department is None or str(request.def_department).strip() == "":
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Department"
                    }

                if request.def_user is None or request.def_user.strip() == "":
                    return {
                        "return_value": 1,
                        "error_message": "Invalid User"
                    }

                if (
                    request.def_descriptor_1 is None or
                    request.def_descriptor_1.strip() == ""
                ):
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Description"
                    }

                if request.def_amount_2 is None:
                    return {
                        "return_value": 1,
                        "error_message": "Invalid Expense Amount"
                    }

                cur.execute("""
                    SELECT d_description
                    FROM retail_accounting.departments
                    WHERE d_id = %s
                """, (
                    request.def_department,
                ))

                dept = cur.fetchone()
                d_description = dept[0] if dept else ""


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
                        NULL,
                        NULL,
                        0,
                        %s,
                        'N'
                    )
                    RETURNING def_id
                """, (
                    str(request.tenant_id),
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_department,
                    request.def_user,
                    request.def_descriptor_1,
                    request.def_descriptor_2,
                    request.def_amount_2
                ))

                inserted_id = cur.fetchone()[0]

                comment = (
                    f"Department - {d_description}, "
                    f"Amount - {request.def_amount_2:.2f}, "
                    f"Identity - {inserted_id}"
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
                """, (
                    str(request.tenant_id),
                    request.def_store,
                    request.def_date,
                    request.def_form_type,
                    request.def_user,
                    comment
                ))


                conn.commit()

                return {
                    "return_value": 0,
                    "error_message": "",
                    "id": inserted_id
                }

    except Exception as e:
        if conn:
            conn.rollback()

        logger.exception("Error in Form106 Insert")

        return {
            "return_value": 1,
            "error_message": f"CSA form106 insertion error, {str(e)}"
        }