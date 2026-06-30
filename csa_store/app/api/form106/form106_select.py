import logging
from uuid import UUID

from fastapi import APIRouter

from app.schemas.form106.form106_select_schema import Form106SelectRequest

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form106",
    tags=["Form106"]
)


@router.post("/select")
def csa_form106_select(request: Form106SelectRequest):
    try:
      
        if request.def_store is None:
            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }


        if request.def_form_type is None or request.def_form_type != 6:
            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        with DBConnection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        d.def_id,
                        d.def_date,
                        d.def_department,
                        dept.d_description,
                        d.def_user,
                        d.def_descriptor_1,
                        d.def_descriptor_2,
                        d.def_amount_2
                    FROM retail_accounting.data_entry_forms d
                    INNER JOIN retail_accounting.departments dept
                        ON d.def_department = dept.d_id
                    WHERE d.def_store = %s
                      AND d.def_form_type = %s
                    ORDER BY d.def_id
                """, (
                    request.def_store,
                    request.def_form_type
                ))

                rows = cur.fetchall()

                result = []

                for row in rows:
                    result.append({
                        "def_id": row[0],
                        "def_date": row[1],
                        "def_department": row[2],
                        "d_description": row[3],
                        "def_user": row[4],
                        "def_descriptor_1": row[5],
                        "def_descriptor_2": row[6],
                        "def_amount_2": float(row[7])
                    })

                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": result
                }

    except Exception as e:
        logger.exception(f"Error in Form106 Select {str(e)}")

        return {
            "return_value": 1,
            "error_message": str(e)
        }