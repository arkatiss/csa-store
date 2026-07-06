import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

from app.schemas.daily.form103.form103_retrieve_by_id_schema import (
    Form103RetrieveByIdRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form103",
    tags=["Form103"]
)


@router.post("/retrieveById")
def form103_retrieve_by_id(
        request: Form103RetrieveByIdRequest):
    """
    Equivalent of:

    csa_Form103_RetrieveByID
    """

    try:

        #
        # VALIDATE ID
        #

        if (
            request.def_id is None
            or
            request.def_id == ""
        ):
            return {
                "return_value": 1,
                "error_message": "Invalid ID"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # CHECK ID EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_accounting.data_entry_forms
                    WHERE tenant_id=%s
                    AND def_id=%s
                """,
                (
                    str(request.tenant_id),
                    request.def_id
                ))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 1,
                        "error_message": "ID Not Found"
                    }

                #
                # FETCH RECORD
                #

                cur.execute("""
                    SELECT
                        de.def_store,
                        de.def_date,
                        de.def_form_type,
                        ft.ft_form_nbr,
                        ft.ft_form_name,
                        de.def_department,
                        d.d_description,
                        de.def_user,
                        de.def_descriptor_1,
                        de.def_descriptor_2,
                        de.def_amount_1,
                        de.def_amount_2
                    FROM retail_accounting.data_entry_forms de
                    INNER JOIN retail_accounting.form_types ft
                        ON de.def_form_type = ft.ft_id
                    INNER JOIN retail_accounting.departments d
                        ON de.def_department = d.d_id
                    WHERE de.def_id=%s
                """,
                (
                    request.def_id,
                ))

                row = cur.fetchone()

                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": {
                        "def_id": request.def_id,
                        "def_store": row[0],
                        "def_date": row[1],
                        "def_form_type": row[2],
                        "ft_form_nbr": row[3],
                        "ft_form_name": row[4],
                        "def_department": row[5],
                        "d_description": row[6],
                        "def_user": row[7],
                        "def_descriptor_1": row[8],
                        "def_descriptor_2": row[9],
                        "def_amount_1": (
                            float(row[10])
                            if row[10] is not None
                            else None
                        ),
                        "def_amount_2": (
                            float(row[11])
                            if row[11] is not None
                            else None
                        )
                    }
                }

    except Exception as ex:

        logger.exception(
            "Error in Form103 RetrieveById"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }