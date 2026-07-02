import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form103.form103_select_schema import (
    Form103SelectRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form103",
    tags=["Form103"]
)


@router.post("/select")
def form103_select(
        request: Form103SelectRequest):
    """
    Equivalent of:

    csa_Form103_Select
    """

    try:

        #
        # VALIDATE STORE
        #

        if (
            request.def_store is None
            or
            request.def_store == ""
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
            request.def_form_type == ""
            or
            request.def_form_type != 2
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        #
        # VALIDATE DEPARTMENT
        #

        if (
            request.def_department is None
            or
            request.def_department == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid Department"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                logger.info(
                    "Fetching Form103 records "
                    "for Store=%s Department=%s",
                    request.def_store,
                    request.def_department
                )

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
                    AND def_department=%s
                    ORDER BY def_id
                """,
                (
                    str(request.tenant_id),
                    request.def_store,
                    request.def_form_type,
                    request.def_department
                ))

                rows = cur.fetchall()

                result = []

                for row in rows:

                    result.append({
                        "def_id": row[0],
                        "def_date": row[1],
                        "def_user": row[2],
                        "def_descriptor_1": row[3],
                        "def_descriptor_2": row[4],
                        "def_amount_1": float(row[5]) if row[5] is not None else None,
                        "def_amount_2": float(row[6]) if row[6] is not None else None
                    })

                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": result
                }

    except Exception as ex:

        logger.exception(
            "Error in Form103 Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }