from fastapi import APIRouter, HTTPException
from app.core.db_utils import DBConnection
import logging

router = APIRouter(
    prefix="/daily/form98",
    tags=["Form98"]
)

logger = logging.getLogger(__name__)


@router.get("/{cb_store}")
def get_form98(cb_store: int):
    """
    Equivalent of csa_Form98_Select
    """

    try:
        # Validation
        if cb_store is None or cb_store <= 0:
            return {
                "return_value": 1,
                "error_message": "Invalid Store",
                "data": []
            }

        query = """
            SELECT
                CB_Date,
                CB_Employee_ID,
                CB_Till,
                CB_Name,
                CB_Sales,
                CB_Voids,
                CB_Returns,
                CB_Checks,
                CB_Gift_Cards_Tendered,
                CB_EBT,
                CB_Credit_Cards,
                CB_WIC,
                CB_Charges,
                CB_Debit_Cards,
                CB_Vendor_Coupons,
                CB_PFC_Coupons,
                CB_Cashier_Over_Short,
                CB_User,
                CB_Promo_Coupons,
                CB_Miscellaneous
            FROM retail_history.cashier_balance
            WHERE CB_Store = %s
            ORDER BY
                CB_Date,
                CB_Employee_ID
        """

        with DBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (cb_store,))

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
        logger.exception("Error fetching Form98 data")

        return {
            "return_value": 1,
            "error_message": str(ex),
            "data": []
        }