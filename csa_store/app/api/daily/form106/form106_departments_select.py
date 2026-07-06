import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form106/departments",
    tags=["Departments"]
)


@router.get("/select")
def csa_departments_select():

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                # Fetch Form104 Departments
                cur.execute("""
                    SELECT
                        d_id,
                        d_description
                    FROM retail_accounting.departments
                    WHERE d_form104_flag='Y'
                    ORDER BY d_description
                """)

                rows = cur.fetchall()

                departments = []

                for row in rows:

                    departments.append({
                        "d_id": row[0],
                        "d_description": row[1]
                    })

                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": departments
                }

    except Exception as e:

        logger.exception(
            "Error in Departments Select"
        )

        return {
            "return_value": 1,
            "error_message": str(e)
        }