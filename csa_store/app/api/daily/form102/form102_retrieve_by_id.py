import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily.form102.form102_retrieve_by_id_schema import Form102RetrieveByIDRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form102",
    tags=["Form102"]
)

@router.post("/retrieveById")
def form102_retrieve_by_id(request: Form102RetrieveByIDRequest):
    """
    Equivalent of:
    csa_Form102_RetrieveByID
    """
    try:
        # VALIDATE ID
        if request.def_id is None:
            return {
                "return_value": 1,
                "error_message": "Invalid ID"
            }

        with DBConnection() as conn:
            with conn.cursor() as cur:

                # CHECK IF ID EXISTS
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

                # FETCH RECORD
                cur.execute("""
                    SELECT
                        def.def_store,
                        def.def_date,
                        def.def_form_type,
                        ft.ft_form_nbr,
                        ft.ft_form_name,
                        def.def_user,
                        def.def_descriptor_1,
                        def.def_descriptor_2,
                        def.def_amount_2
                    FROM retail_accounting.data_entry_forms def
                    INNER JOIN retail_accounting.form_types ft
                        ON def.def_form_type = ft.ft_id
                    WHERE def.def_id=%s
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
                        "def_user": row[5],
                        "def_descriptor_1": row[6],
                        "def_descriptor_2": row[7],
                        "def_amount_2": float(row[8]) if row[8] is not None else 0
                    }
                }

    except Exception as ex:
        logger.exception("Error in Form102 Retrieve By ID")
        return {
            "return_value": 1,
            "error_message": str(ex)
        }
