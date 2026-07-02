import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form104",
    tags=["Form104"]
)


@router.get("/account-descriptions")
def form104_account_descriptions_select():
    """
    Equivalent of:

    csa_Form104AccountDescriptions_Select
    """

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                logger.info(
                    "Fetching Form104 account descriptions"
                )

                cur.execute("""
                    SELECT
                        f104_ad_description
                    FROM retail_accounting.form104_account_descriptions
                    WHERE f104_ad_status='A'
                    ORDER BY f104_ad_description
                """)

                rows = cur.fetchall()

                result = [
                    {
                        "f104_ad_description": row[0]
                    }
                    for row in rows
                ]

                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": result
                }

    except Exception as ex:

        logger.exception(
            "Error in Form104AccountDescriptions Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }