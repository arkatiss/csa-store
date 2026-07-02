import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection
from app.schemas.daily.form106.form106_retrieve_by_id_schema import (
    Form106RetrieveByIDRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form106",
    tags=["Form106"]
)


@router.post("/retrievebyid")
def csa_form106_retrieve_by_id(request: Form106RetrieveByIDRequest):

    try:

        # Validate ID
        if request.def_id is None:
            return {
                "return_value": 1,
                "error_message": "Invalid ID"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                # Check ID Exists
                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_accounting.data_entry_forms
                    WHERE def_id=%s
                """,
                (
                    request.def_id,
                ))

                count = cur.fetchone()[0]

                if count == 0:
                    return {
                        "return_value": 1,
                        "error_message": "ID Not Found"
                    }

                # Retrieve Form106 Record
                cur.execute("""
                    SELECT
                        d.def_store,
                        d.def_date,
                        d.def_form_type,
                        f.ft_form_nbr,
                        f.ft_form_name,
                        d.def_department,
                        dep.d_description,
                        d.def_user,
                        d.def_descriptor_1,
                        d.def_descriptor_2,
                        d.def_amount_2
                    FROM retail_accounting.data_entry_forms d
                    INNER JOIN retail_accounting.form_types f
                        ON d.def_form_type = f.ft_id
                    INNER JOIN retail_accounting.departments dep
                        ON d.def_department = dep.d_id
                    WHERE d.def_id=%s
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
                        "def_amount_2": row[10]
                    }
                }

    except Exception as e:

        logger.exception(
            "Error in Form106 Retrieve By ID"
        )

        return {
            "return_value": 1,
            "error_message": str(e)
        }