import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form122",
    tags=["Form122"]
)


@router.get("/select/{psi_store}")
def form122_select(
        psi_store: int):
    """
    Equivalent of:

    csa_Form122_Select
    """

    try:

        #
        # VALIDATION
        #

        if psi_store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # CHECK RECORD EXISTS
                #

                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_history.postage_stamp_inventory
                    WHERE psi_store=%s
                """,
                (
                    psi_store,
                ))

                count = cur.fetchone()[0]

                if count == 0:

                    return {
                        "return_value": 3,
                        "error_message": "No Rows Found"
                    }

                logger.info(
                    f"Fetching Form122 records "
                    f"for Store={psi_store}"
                )

                #
                # FETCH DATA
                #

                cur.execute("""
                    SELECT
                        psi_date,
                        psi_beginning_books,
                        psi_books_received,
                        psi_money_collected,
                        psi_books_sold,
                        psi_books_in_till,
                        psi_books_in_safe,
                        psi_books_in_office,
                        psi_process_flag
                    FROM retail_history.postage_stamp_inventory
                    WHERE psi_store=%s
                    ORDER BY psi_date ASC
                """,
                (
                    psi_store,
                ))

                rows = cur.fetchall()

                data = []

                for row in rows:

                    data.append({
                        "psi_date": row[0],
                        "psi_beginning_books": row[1],
                        "psi_books_received": row[2],
                        "psi_money_collected": float(row[3])
                        if row[3] is not None
                        else 0,
                        "psi_books_sold": row[4],
                        "psi_books_in_till": row[5],
                        "psi_books_in_safe": row[6],
                        "psi_books_in_office": row[7],
                        "psi_process_flag": row[8]
                    })

                return {
                    "return_value": 0,
                    "data": data
                }

    except Exception as ex:

        logger.exception(
            "Error in Form122 Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }