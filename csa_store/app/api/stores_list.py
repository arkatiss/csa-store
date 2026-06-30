from fastapi import APIRouter, HTTPException
from app.core.db_utils import DBConnection
import logging

router = APIRouter(
    prefix="/stores",
    tags=["Form98"]
)

logger = logging.getLogger(__name__)


@router.get("")
def get_form98():
    """
    Equivalent of csa_Form98_Select
    """

    try:
        query = """
            SELECT tenant_id, sc_store, sc_eod_last_run, sc_eow_last_run from retail_accounting.store_configuration"""

        with DBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)

                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                result = [
                    dict(zip(columns, row))
                    for row in rows
                ]

        return {
            "return_value": 0,
            "error_message": "",
            "count": len(result),
            "data": result
        }

    except Exception as ex:
        logger.exception("Error fetching Stores data")

        return {
            "return_value": 1,
            "error_message": str(ex),
            "data": []
        }