import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.gross_profit_and_inventory.wtd_gross_profit_inventory_retrievebyid_schema import WTDGrossProfitInventoryRetrieveByIDRequest, WTDGrossProfitInventorySelectResponse, WTDGrossProfitInventoryItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/week_to_date/wtd_gross_profit_inventory",
    tags=["Week To Date Gross Profit And Inventory"]
)

@router.post("/wtd_gross_profit_inventory_retrievebyid", response_model=WTDGrossProfitInventorySelectResponse)
def csa_wtd_gross_profit_inventory_select(request: WTDGrossProfitInventoryRetrieveByIDRequest):
    """
    Equivalent of:
    csa_WTDGrossProfitInventory_Select
    """
    try:
        if request.wgi_department is None:
            return WTDGrossProfitInventoryRetrieveByIDRequest(
                return_value=1,
                error_message="Invalid Department",
                data=None
            )


        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if row exists
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_gross_profit_inventory
                    WHERE wgi_department = %s
                """, (request.wgi_department,))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return WTDGrossProfitInventorySelectResponse(
                        return_value=3,
                        error_message="Record not found",
                        data=None
                    )

                # Retrieve values using INNER JOIN
                cur.execute("""
                    SELECT 	wgi_department,
                            d_description,
                            wgi_gross_profit,
                            sda_gp_mf_account_nbr,
                            wgi_ending_inventory,
                            sda_ei_mf_account_nbr
                    FROM retail_accounting.wtd_gross_profit_inventory
                    INNER JOIN retail_accounting.departments
                        ON wgi_department = d_id
                    INNER JOIN retail_accounting.store_department_account
                        ON wgi_department = sda_department
                        AND wgi_store = sda_store
                    WHERE wgi_department = %s
                    AND (CAST(sda_gp_mf_account_nbr AS INT) > 0
                         OR CAST(sda_ei_mf_account_nbr AS INT) > 0)
                """, (request.wgi_department,))
                
                rows = cur.fetchall()
                data = []
                for row in rows:
                    item = WTDGrossProfitInventoryItem(
                        wgi_department=row[0],
                        d_description=row[1],
                        wgi_gross_profit=row[2],
                        sda_gp_mf_account_nbr=row[3],
                        wgi_ending_inventory=row[4],
                        sda_ei_mf_account_nbr=row[5]
                    )
                    data.append(item)
                    
                return WTDGrossProfitInventorySelectResponse(
                    return_value=0,
                    error_message="",
                    data=data
                )

    except Exception as ex:
        logger.exception("Error in WTDGrossProfitInventory_Select")
        return WTDGrossProfitInventorySelectResponse(
            return_value=1,
            error_message="Select WTD Gross Profit Inventory Failed",
            data=None
        )
