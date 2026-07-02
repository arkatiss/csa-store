import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form104",
    tags=["Form104"]
)


@router.get("/select/{store}/{form_type}")
def form104_select(
        store: int,
        form_type: int):
    """
    Equivalent of:

    csa_Form104_Select
    """

    try:

        #
        # VALIDATIONS
        #

        if store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if (
            form_type is None
            or
            form_type != 3
        ):

            return {
                "return_value": 1,
                "error_message": "Invalid Form Type"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                logger.info(
                    f"Fetching Form104 records "
                    f"for Store={store}"
                )

                cur.execute("""
                    SELECT
                        def_id,
                        def_date,
                        def_department,
                        d_description,
                        def_user,
                        def_descriptor_1,
                        def_descriptor_2,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    INNER JOIN retail_accounting.departments
                        ON def_department = d_id
                    WHERE def_store=%s
                    AND def_form_type=%s
                    ORDER BY def_id
                """,
                (
                    store,
                    form_type
                ))

                rows = cur.fetchall()

                data = []

                for row in rows:

                    data.append({
                        "def_id": row[0],
                        "def_date": row[1],
                        "def_department": row[2],
                        "department_description": row[3],
                        "def_user": row[4],
                        "def_descriptor_1": row[5],
                        "def_descriptor_2": row[6],
                        "def_amount_2": float(row[7])
                        if row[7] is not None
                        else 0
                    })

                return {
                    "return_value": 0,
                    "data": data
                }

    except Exception as ex:

        logger.exception(
            "Error in Form104 Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }