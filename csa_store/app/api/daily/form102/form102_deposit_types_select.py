import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/form102",
    tags=["Form102"]
)

@router.get("/depositTypes/select")
def csa_deposit_types_select():
    """
    Equivalent of:
    csa_DepositTypes_Select
    """
    try:
        with DBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        dt_type,
                        dt_description
                    FROM retail_accounting.deposit_types
                """)
                
                rows = cur.fetchall()
                response_data = []
                
                for row in rows:
                    response_data.append({
                        "dt_type": row[0],
                        "dt_description": row[1]
                    })
                    
                return {
                    "return_value": 0,
                    "error_message": "",
                    "data": response_data
                }

    except Exception as ex:
        logger.exception("Error in DepositTypes Select")
        return {
            "return_value": 1,
            "error_message": str(ex)
        }
