import logging

from fastapi import APIRouter

from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily/form111",
    tags=["Form111"]
)


@router.get("/form111-accountDescriptions")
def form111_account_descriptions_select():
    """
    Equivalent of:

    csa_Form111AccountDescriptions_Select
    """

    try:

        with DBConnection() as conn:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        f111_ad_description
                    FROM retail_accounting.form111_account_descriptions
                    WHERE f111_ad_user_select='Y'
                    AND f111_ad_status='A'
                    ORDER BY f111_ad_description
                """)

                rows = cur.fetchall()

                return {
                    "return_value": 0,
                    "data": [
                        {
                            "f111ad_description": row[0]
                        }
                        for row in rows
                    ]
                }

    except Exception as ex:

        logger.exception(
            "Error in Form111 Account Descriptions Select"
        )

        return {
            "return_value": 1,
            "error_message": str(ex)
        }