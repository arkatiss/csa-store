import logging

from datetime import date

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form122",
    tags=["Form122"]
)


@router.get("/retrievebyid/{psi_store}/{psi_date}")
def form122_retrieve_by_id(
        psi_store: int,
        psi_date: date):
    """
    Equivalent of:

    csa_Form122_RetrieveByID
    """

    try:

        #
        # VALIDATIONS
        #

        if psi_store is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        if psi_date is None:

            return {
                "return_value": 1,
                "error_message": "Invalid Store"
            }

        with DBConnection() as conn:

            with conn.cursor() as cur:

                #
                # CHECK STORE EXISTS
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

                #
                # FETCH RECORD
                #

                cur.execute("""
                    SELECT
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
                    AND psi_date=%s
                    ORDER BY psi_date DESC
                """,
                (
                    psi_store,
                    psi_date
                ))

                row = cur.fetchone()

                if not row:

                    return {
                        "return_value": 3,
                        "error_message": "No Rows Found"
                    }

                return {
                    "return_value": 0,
                    "data": {
                        "psi_store": psi_store,
                        "psi_date": psi_date,
                        "psi_beginning_books": row[0],
                        "psi_books_received": row[1],
                        "psi_money_collected": float(row[2])
                        if row[2] is not None
                        else 0,
                        "psi_books_sold": row[3],
                        "psi_books_in_till": row[4],
                        "psi_books_in_safe": row[5],
                        "psi_books_in_office": row[6],
                        "psi_process_flag": row[7]
                    }
                }

    except Exception as ex:

        logger.exception(
            "Error in Form122 Retrieve By ID"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }