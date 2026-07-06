import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form111.form111_select_schema import (
    Form111SelectRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form111",
    tags=["Form111"]
)


@router.post("/select")
def form111_select(
        request: Form111SelectRequest):
    """
    Equivalent of:

    csa_Form111_Select
    """

    try:

        #
        # VALIDATE STORE
        #

        if (
            request.def_store is None
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        #
        # VALIDATE FORM TYPE
        #

        if (
            request.def_form_type is None
            or
            request.def_form_type != 7
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        def_id,
                        def_date,
                        def_user,
                        def_descriptor_1,
                        def_descriptor_2,
                        def_amount_1,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_store=%s
                    AND def_form_type=%s
                    ORDER BY def_id
                """,
                (
                    str(request.tenant_id),
                    request.def_store,
                    request.def_form_type
                ))

                rows = cur.fetchall()

                response_data = []

                for row in rows:

                    response_data.append({
                        "def_id": row[0],
                        "def_date": row[1],
                        "def_user": row[2],
                        "def_descriptor_1": row[3],
                        "def_descriptor_2": row[4],
                        "def_amount_1": float(row[5])
                        if row[5] is not None
                        else 0,
                        "def_amount_2": float(row[6])
                        if row[6] is not None
                        else 0
                    })

                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": response_data
                }

    except Exception as ex:

        logger.exception(
            "Error in Form111 Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }