import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form105a",
    tags=["Form105A"]
)


@router.get("/form105a-ar-payment-types")
def ar_payment_types_select():
    """
    Equivalent of:

    csa_ARPaymentTypes_Select
    """

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                logger.info(
                    "Fetching AR Payment Types"
                )

                cur.execute("""
                    SELECT
                        arpt_type,
                        arpt_description
                    FROM retail_accounting.ar_payment_types
                    ORDER BY arpt_type
                """)

                rows = cur.fetchall()

                data = []

                for row in rows:

                    data.append({
                        "arpt_type": row[0],
                        "arpt_description": row[1]
                    })

                return {
                    "return_value": 0,
                    "data": data
                }

    except Exception as ex:

        logger.exception(
            "Error in AR Payment Types Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }