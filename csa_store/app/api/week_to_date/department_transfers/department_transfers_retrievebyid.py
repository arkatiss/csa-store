import os
import logging
from typing import Dict, Any
from fastapi import APIRouter
from psycopg2.extras import RealDictCursor
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.department_transfers.department_transfers_retrievebyid_schema import DepartmentTransferRequest, DepartmentTransferResponse



# Configure logging for the application
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/week_to_date/departments_transfers",
    tags=["Week To Date Department Transfers"]
)


def execute_csa_department_transfers_retrieve_by_id(ddt_id: int) -> Dict[str, Any]:
    """
    Helper function that replicates the logic of the stored procedure
    [dbo].[csa_DepartmentTransfers_RetrieveByID].

    Logic:
    1. Validate input ID.
    2. Check if the record exists in retail_accounting.daily_department_transfers.
    3. Retrieve record details with joined department descriptions.
    """

    # Initialize default response structure matching the procedure's output parameters
    result = {
        "ddt_store": None,
        "ddt_to_store": None,
        "ddt_date": None,
        "ddt_from_department": None,
        "d_from_department_desc": None,
        "ddt_to_department": None,
        "d_to_department_desc": None,
        "ddt_item_quantity": None,
        "ddt_item_description": None,
        "ddt_user": None,
        "ddt_retail_amount": None,
        "ddt_cost_amount": None,
        "Return_Value": 0,
        "Error_Message": None
    }

    # Logic: If @DDT_ID is null or @DDT_ID = ''
    if ddt_id is None or str(ddt_id).strip() == '':
        logger.warning("Validation failed: ddt_id is null or empty.")
        result["Return_Value"] = 1
        result["Error_Message"] = "Invalid ID"
        return result

    try:
        with DBConnection() as conn:
            with conn.cursor() as cursor:
                # Logic: Select @Count = count(*) From retail_accounting.daily_department_transfers
                # Note: 'with (nolock)' is T-SQL specific; PostgreSQL uses MVCC and doesn't require it for this logic.
                count_query = """
                    SELECT count(*) 
                    FROM retail_accounting.daily_department_transfers 
                    WHERE ddt_id = %s
                """
                cursor.execute(count_query, (ddt_id,))
                count = cursor.fetchone()[0]

                # Logic: If @Count = 0
                if count == 0:
                    logger.info(f"Record not found for DDT_ID: {ddt_id}")
                    result["Return_Value"] = 1
                    result["Error_Message"] = "ID Not Found"
                    return result

                # Logic: Main Select statement with Inner Joins
                main_query = """
                    SELECT	
                        ddt_store,
                        ddt_to_store,
                        ddt_date,
                        ddt_from_department,
                        D1.d_description AS d_from_department_desc,
                        ddt_to_department,
                        D2.d_description AS d_do_description_desc,
                        ddt_item_quantity,
                        ddt_item_description,
                        ddt_user,
                        ddt_retail_amount,
                        ddt_cost_amount
                    FROM retail_accounting.daily_department_transfers
                    INNER JOIN retail_accounting.departments D1
                        ON ddt_from_department = D1.d_id
                    INNER JOIN retail_accounting.departments D2
                        ON ddt_to_department = D2.d_id
                    WHERE ddt_id = %s
                """
                cursor.execute(main_query, (ddt_id,))
                row = cursor.fetchone()

                if row:
                    result["ddt_id"] = ddt_id
                    result["ddt_store"] = row[0]
                    result["ddt_to_store"] = row[1]
                    result["ddt_date"] = row[2]
                    result["ddt_from_department"] = row[3]
                    result["d_from_department_desc"] = row[4]
                    result["ddt_to_department"] = row[5]
                    result["d_to_department_desc"] = row[6]
                    result["ddt_item_quantity"] = row[7]
                    result["ddt_item_description"] = row[8]
                    result["ddt_user"] = row[9]
                    result["ddt_retail_amount"] = row[10]
                    result["ddt_cost_amount"] = row[11]
                    result["Return_Value"] = 0
                    logger.info(f"Successfully retrieved record for DDT_ID: {ddt_id}")
                else:
                    # This case handles if the record was deleted between the count and the select
                    result["Return_Value"] = 1
                    result["Error_Message"] = "ID Not Found"

    except Exception as e:
        logger.error(f"Database error occurred: {str(e)}")
        result["Return_Value"] = 1
        result["Error_Message"] = f"Database Error: {str(e)}"

    return result


@router.post("/retrievebyid", response_model=DepartmentTransferResponse)
async def retrieve_department_transfer_by_id(request: DepartmentTransferRequest):
    """
    API Endpoint to retrieve a specified row from the DailyDepartmentTransfers table.

    This endpoint replicates the functionality of the T-SQL stored procedure:
    [dbo].[csa_DepartmentTransfers_RetrieveByID]
    """
    logger.info(f"Received request to retrieve Department Transfer with ID: {request.ddt_id}")

    # Core Logic Execution
    # The core logic is encapsulated in the helper function to maintain clean API structure
    # while ensuring 100% functional equivalence to the original T-SQL procedure.
    try:
        procedure_result = execute_csa_department_transfers_retrieve_by_id(request.ddt_id)

        # The procedure logic returns Return_Value = 1 for business logic errors (Invalid ID, Not Found)
        # We return the full object as per the procedure's output parameter design.
        return DepartmentTransferResponse(**procedure_result)

    except Exception as e:
        logger.error(f"Unexpected error in API layer: {str(e)}")
        # Fallback for unexpected system errors
        return DepartmentTransferResponse(
            Return_Value=1,
            Error_Message="An unexpected internal error occurred."
        )