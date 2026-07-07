import os
import logging
from fastapi import APIRouter
from psycopg2.extras import RealDictCursor
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.department_transfers.department_transfers_select_schema import DepartmentTransferRequest, DepartmentTransferItem, DepartmentTransferResponse



# Configure logging for the application
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/week_to_date/departments_transfers",
    tags=["Week To Date Department Transfers"]
)


@router.post("/select")
async def csa_department_transfers_select(request: DepartmentTransferRequest):
    """
    Show all department transfers for a selected store.

    This API replicates the logic of the stored procedure [dbo].[csa_DepartmentTransfers_Select].
    It validates the store ID, performs a join between transfers and departments,
    and returns the transfer details ordered by ID.
    """
    logger.info(f"Starting csa_department_transfers_select for store ID: {request.ddt_store}")

    # Logic: IF @DDT_Store is null or @DDT_Store = ''
    # In Python, we check for None or empty values.
    if request.ddt_store is None or str(request.ddt_store).strip() == "":
        logger.warning("Validation failed: Invalid Store ID provided")
        return DepartmentTransferResponse(
            return_value=1,
            error_message="Invalid Store",
            data=[]
        )

    try:
        with DBConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # SQL Query translated from the T-SQL SELECT statement
                # Includes joins with the departments table for both 'From' and 'To' descriptions
                query = """
                    SELECT 
                        DDT_ID,
                        DDT_Date,
                        DDT_From_Department,
                        D1.D_Description AS d_from_department_desc,
                        DDT_To_Department,
                        D2.D_Description AS d_to_department_desc,
                        DDT_Item_Quantity,
                        DDT_Item_Description,
                        DDT_User,
                        DDT_Retail_Amount,
                        DDT_Cost_Amount,
                        DDT_To_Store
                    FROM 
                        retail_accounting.daily_department_transfers
                    INNER JOIN 
                        retail_accounting.departments D1 ON DDT_From_Department = D1.D_ID
                    INNER JOIN 
                        retail_accounting.departments D2 ON DDT_To_Department = D2.D_ID
                    WHERE 
                        DDT_Store = %s
                    ORDER BY 
                        DDT_ID
                """

                logger.info(f"Executing query for store {request.ddt_store}")
                cur.execute(query, (request.ddt_store,))
                rows = cur.fetchall()

                # Map the database rows to the Pydantic model list
                transfer_list = []
                for row in rows:
                    transfer_list.append(DepartmentTransferItem(
                        ddt_id=row['ddt_id'],
                        ddt_date=row['ddt_date'],
                        ddt_from_department=row['ddt_from_department'],
                        d_from_department_desc=row['d_from_department_desc'],
                        ddt_to_department=row['ddt_to_department'],
                        d_to_department_desc=row['d_to_department_desc'],
                        ddt_item_quantity=row['ddt_item_quantity'],
                        ddt_item_description=row['ddt_item_description'],
                        ddt_user=row['ddt_user'],
                        ddt_retail_amount=row['ddt_retail_amount'],
                        ddt_cost_amount=row['ddt_cost_amount'],
                        ddt_to_store=row['ddt_to_store']
                    ))

                logger.info(f"Query successful. Found {len(transfer_list)} records.")

                # Logic: Select @Return_Value = 0, Return 0
                return DepartmentTransferResponse(
                    return_value=0,
                    error_message="",
                    data=transfer_list
                )

    except Exception as e:
        logger.error(f"An error occurred during database execution: {str(e)}")
        # Return failure status similar to the procedure's error handling
        return DepartmentTransferResponse(
            return_value=1,
            error_message=f"Internal Server Error: {str(e)}",
            data=[]
        )