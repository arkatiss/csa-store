import logging

from fastapi import APIRouter

from datetime import timedelta

from app.core.db_utils import DBConnection

from app.schemas.form111.form111_insert_schema import (
    Form111InsertRequest
)

from app.utils.form98_helper import (
    get_week_ending_date
)

from app.utils.form111_helper import (
    update_dsc_with_form111,
    insert_form111_insert_audit
)

router = APIRouter(
    prefix="/form111",
    tags=["Form111"]
)

@router.post("/insert")
def form111_insert(
        request: Form111InsertRequest):
    if request.def_store is None:
        return {
            "return_value": 1,
            "error_message": "Invalid Store"
        }

    if request.def_form_type != 7:
        return {
            "return_value": 1,
            "error_message": "Invalid Form Type"
        }

    if (
            request.def_user is None
            or
            request.def_user.strip() == ""
    ):
        return {
            "return_value": 1,
            "error_message": "Invalid User"
        }

    if (
            request.def_descriptor_1 is None
            or
            request.def_descriptor_1.strip() == ""
    ):
        return {
            "return_value": 1,
            "error_message": "Invalid Description"
        }

    if request.def_amount_1 is None:
        return {
            "return_value": 1,
            "error_message": "Invalid Retail"
        }

    if request.def_amount_2 is None:
        return {
            "return_value": 1,
            "error_message": "Invalid Cost"
        }

    with DBConnection() as conn:

        with conn.cursor() as cur:

            week_ending_date = get_week_ending_date(
                cur,
                request.def_store
            )

            if (
                    request.def_date <
                    (week_ending_date - timedelta(days=7))
                    or
                    request.def_date >
                    (week_ending_date + timedelta(days=1))
            ):
                return {
                    "return_value": 1,
                    "error_message": "Invalid Date"
                }

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
                    NULL,
                    %s,
                    %s,
                    %s,
                    NULL,
                    NULL,
                    %s,
                    %s,
                    'N'
                )
                RETURNING def_id
            """,
                        (
                            str(request.tenant_id),
                            request.def_store,
                            request.def_date,
                            request.def_form_type,
                            request.def_user,
                            request.def_descriptor_1,
                            request.def_descriptor_2,
                            request.def_amount_1,
                            request.def_amount_2
                        ))

            def_id = cur.fetchone()[0]

            update_dsc_with_form111(
                cur,
                request.tenant_id,
                request.def_store,
                week_ending_date
            )

            conn.commit()

            insert_form111_insert_audit(
                cur,
                request.tenant_id,
                request.def_store,
                request.def_date,
                request.def_form_type,
                request.def_user,
                request.def_amount_2,
                def_id
            )

            conn.commit()

            return {
                "return_value": 0,
                "message": "Record Inserted Successfully",
                "def_id": def_id
            }