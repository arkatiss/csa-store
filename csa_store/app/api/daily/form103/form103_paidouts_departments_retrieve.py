from fastapi import APIRouter
import logging

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form103",
    tags=["Form103"]
)


@router.get("/paidouts/departments/{store}")
def paidouts_departments_select(store: int):
    """
    Equivalent of:

    csa_PaidOutsDepartments_Select
    """

    try:

        logger.info(
            f"Fetching Form103 departments "
            f"for store {store}"
        )

        with DBConnection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        d.d_id,
                        d.d_description
                    FROM retail_accounting.departments d
                    INNER JOIN retail_accounting.store_department_account sda
                        ON d.d_id = sda.sda_department
                    WHERE
                        sda.sda_po_mf_account_nbr IS NOT NULL
                        AND TRIM(sda.sda_po_mf_account_nbr) <> ''
                        AND TRIM(sda.sda_po_mf_account_nbr) <> '0'
                        AND sda.sda_store = %s
                    ORDER BY d.d_description
                    """,
                    (store,)
                )

                rows = cur.fetchall()

                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": [
                        {
                            "d_id": row[0],
                            "d_description": row[1]
                        }
                        for row in rows
                    ]
                }

    except Exception as ex:

        logger.exception(
            "Error while fetching departments"
        )

        return {
            "return_value": 1,
            "error_message": str(ex),
            "data": []
        }