import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form104",
    tags=["Form104"]
)


@router.get("/retrievebyID/{def_id}")
def form104_retrieve_by_id(
        def_id: int):
    """
    Equivalent of:

    csa_Form104_RetrieveByID
    """

    try:

        #
        # VALIDATIONS
        #

        if def_id is None:

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
                    WHERE def_id=%s
                """,
                (
                    def_id,
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
                        def_store,
                        def_date,
                        def_form_type,
                        ft_form_nbr,
                        ft_form_name,
                        def_department,
                        d_description,
                        def_user,
                        def_descriptor_1,
                        def_descriptor_2,
                        def_amount_2
                    FROM retail_accounting.data_entry_forms
                    INNER JOIN retail_accounting.form_types
                        ON def_form_type = ft_id
                    INNER JOIN retail_accounting.departments
                        ON def_department = d_id
                    WHERE def_id=%s
                """,
                (
                    def_id,
                ))

                row = cur.fetchone()

                print(f"Retrieved Row: {row}")

                return {
                    "return_value": 0,
                    "data": {
                        "def_id": def_id,
                        "def_store": row[0],
                        "def_date": row[1],
                        "def_form_type": row[2],
                        "ft_form_nbr": row[3],
                        "ft_form_name": row[4],
                        "def_department": row[5],
                        "department_description": row[6],
                        "def_user": row[7],
                        "def_descriptor_1": row[8],
                        "def_descriptor_2": row[9],
                        "def_amount_2": float(row[10])
                        if row[10] is not None
                        else 0
                    }
                }

    except Exception as ex:

        logger.exception(
            "Error in Form104 Retrieve By ID"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }