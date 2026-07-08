import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.gross_profit_and_inventory.wtd_gross_profit_inventory_schema import (
    WTDGrossProfitInventoryUpdateRequest, 
    WTDGrossProfitInventoryUpdateResponse
)
from app.utils.week_to_date.gross_profit_inventory_helper import (
    get_department_description,
    insert_audit_record
)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/week_to_date/wtd_gross_profit_inventory",
    tags=["Week To Date Gross Profit Inventory"]
)

@router.put("/update", response_model=WTDGrossProfitInventoryUpdateResponse)
def csa_wtd_gross_profit_inventory_update(request: WTDGrossProfitInventoryUpdateRequest):
    """
    Python API implementation of the stored procedure:
    dbo.csa_WTDGrossProfitInventory_Update
    
    This endpoint updates the Gross Profit and Ending Inventory for a specific 
    store, department, and week ending date, while maintaining an audit trail.
    """
    try:
        # --- Initial Validations ---
        
        # If @WGI_Store is null or @WGI_Store = ''
        if request.wgi_store is None:
            return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="Invalid Store")

        # If @WGI_Week_Ending_Date is null or @WGI_Week_Ending_Date = ''
        if request.wgi_week_ending_date is None:
            return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="Invalid Week Ending Date")

        # If @WGI_Department is null or @WGI_Department = ''
        if request.wgi_department is None:
            return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="Invalid Department")

        # If @User is null or @User = ''
        if not request.user or str(request.user).strip() == '':
            return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="Invalid User")

        # IF (@WGI_Gross_Profit is null or convert(varchar(12),@WGI_Gross_Profit) = '') and
        #    (@WGI_Ending_Inventory is null or convert(varchar(12),@WGI_Ending_Inventory) = '')
        if request.wgi_gross_profit is None and request.wgi_ending_inventory is None:
            return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="No Updateable Attributes Received")

        with DBConnection() as conn:
            with conn.cursor() as cur:
                
                # --- Check if Record Exists ---
                # Select @Count = count(*) From retail_accounting.wtd_gross_profit_inventory ...
                cur.execute("""
                    SELECT count(*)
                    FROM retail_accounting.wtd_gross_profit_inventory
                    WHERE WGI_Store = %s 
                      AND WGI_Week_Ending_Date = %s 
                      AND WGI_Department = %s
                """, (request.wgi_store, request.wgi_week_ending_date, request.wgi_department))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="Record Not Found")

                # --- Fetch Old Values ---
                # Select @Old_WGI_Gross_Profit = WGI_Gross_Profit, @Old_WGI_Ending_Inventory = WGI_Ending_Inventory ...
                cur.execute("""
                    SELECT WGI_Gross_Profit, WGI_Ending_Inventory
                    FROM retail_accounting.wtd_gross_profit_inventory
                    WHERE WGI_Store = %s 
                      AND WGI_Week_Ending_Date = %s 
                      AND WGI_Department = %s
                """, (request.wgi_store, request.wgi_week_ending_date, request.wgi_department))
                
                old_row = cur.fetchone()
                old_wgi_gross_profit = float(old_row[0]) if old_row[0] is not None else 0.0
                old_wgi_ending_inventory = float(old_row[1]) if old_row[1] is not None else 0.0

                # --- Check for Changes ---
                # If @Old_WGI_Gross_Profit = @WGI_Gross_Profit and @Old_WGI_Ending_Inventory = @WGI_Ending_Inventory
                if (old_wgi_gross_profit == request.wgi_gross_profit and 
                    old_wgi_ending_inventory == request.wgi_ending_inventory):
                    return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="No Updates Detected")

                # --- Fetch Department Description ---
                # Select @D_Description = D_Description From retail_accounting.departments ...
                d_description = get_department_description(cur, request.wgi_department)

                try:
                    # --- Update Record ---
                    # BEGIN TRANSACTION logic is handled by DBConnection context manager
                    # Update retail_accounting.wtd_gross_profit_inventory ...
                    cur.execute("""
                        UPDATE retail_accounting.wtd_gross_profit_inventory
                        SET WGI_Gross_Profit = %s,
                            WGI_Ending_Inventory = %s
                        WHERE WGI_Store = %s 
                          AND WGI_Week_Ending_Date = %s 
                          AND WGI_Department = %s
                    """, (
                        request.wgi_gross_profit, 
                        request.wgi_ending_inventory, 
                        request.wgi_store, 
                        request.wgi_week_ending_date, 
                        request.wgi_department
                    ))
                    
                    # Commit is handled by __exit__ of DBConnection if no exception occurs
                    # but we can explicitly commit if needed for logic flow
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    logger.exception("Update Failed in csa_WTDGrossProfitInventory_Update")
                    return WTDGrossProfitInventoryUpdateResponse(return_value=1, error_message="Update Failed")

                # --- Audit Logging ---
                
                # If @Old_WGI_Gross_Profit != @WGI_Gross_Profit
                if old_wgi_gross_profit != request.wgi_gross_profit:
                    comment = (f"Gross Profit for Dept. {d_description} Changed From : "
                               f"{old_wgi_gross_profit:.2f} To : {request.wgi_gross_profit:.2f}")
                    insert_audit_record(
                        cur, 
                        request.tenant_id, 
                        request.wgi_store, 
                        request.wgi_week_ending_date, 
                        request.user, 
                        comment
                    )

                # If @Old_WGI_Ending_Inventory != @WGI_Ending_Inventory
                if old_wgi_ending_inventory != request.wgi_ending_inventory:
                    comment = (f"Ending Inventory for Dept. {d_description} Changed From : "
                               f"{old_wgi_ending_inventory:.2f} To : {request.wgi_ending_inventory:.2f}")
                    insert_audit_record(
                        cur, 
                        request.tenant_id, 
                        request.wgi_store, 
                        request.wgi_week_ending_date, 
                        request.user, 
                        comment
                    )

                # Final Commit for Audit Logs
                conn.commit()

                # Select @Return_Value = 0
                return WTDGrossProfitInventoryUpdateResponse(return_value=0, error_message="")

    except Exception as ex:
        logger.exception("Unexpected error in csa_wtd_gross_profit_inventory_update")
        return WTDGrossProfitInventoryUpdateResponse(
            return_value=1,
            error_message="Internal Server Error"
        )