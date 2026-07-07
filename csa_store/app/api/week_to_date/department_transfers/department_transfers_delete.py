import os
import logging
from datetime import datetime
from fastapi import APIRouter
from psycopg2.extras import RealDictCursor
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.department_transfers.department_transfers_delete_schema import DepartmentTransferDeleteRequest, DepartmentTransferDeleteResponse
from app.utils.week_to_date.department_transfers_helper import calculate_week_ending_date, validate_transfer_date




# Configure logging for the application
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/week_to_date/departments_transfers",
    tags=["Week To Date Department Transfers"]
)


@router.delete("/delete", response_model=DepartmentTransferDeleteResponse)
def delete_department_transfer(request_data: DepartmentTransferDeleteRequest):
    """
    csa_DepartmentTransfers_Delete
    Delete specified row from the DailyDepartmentTransfers table by ID.

    This API performs the following:
    1. Validates the input ID.
    2. Retrieves existing record details for auditing.
    3. Deletes the record from retail_accounting.daily_department_transfers.
    4. Logs the deletion in retail_history.audit.
    """

    # Local variables to hold retrieved data for audit (Equivalent to Declare @I_...)
    i_ddt_store = None
    i_ddt_date = None
    i_ddt_cost_amount = None

    # 1. Validate Identity (Equivalent to If @DDT_ID is null or @DDT_ID = '')
    if not request_data.ddt_id:
        logger.warning("Delete failed: Invalid Identity provided.")
        return DepartmentTransferDeleteResponse(
            return_value=1,
            error_message="Invalid Identity"
        )

    try:
        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 2. Select existing data (Equivalent to Select @I_DDT_Store = DDT_Store...)
                # Note: We include tenant_id as it is part of the primary key in the provided schema
                select_query = """
                    SELECT ddt_store, ddt_date, ddt_cost_amount
                    FROM retail_accounting.daily_department_transfers
                    WHERE ddt_id = %s
                """
                cur.execute(select_query, (request_data.ddt_id,))
                row = cur.fetchone()

                # 3. Check if row exists (Equivalent to If @I_DDT_Store is null or @I_DDT_Store = '')
                if not row:
                    logger.warning(f"Delete failed: Row not found for ID {request_data.ddt_id}")
                    return DepartmentTransferDeleteResponse(
                        return_value=1,
                        error_message="Row not found for delete"
                    )

                i_ddt_store = row[0]
                i_ddt_date = row[1]
                i_ddt_cost_amount = row[2]

                # 4. BEGIN TRANSACTION and Delete (Equivalent to BEGIN TRANSACTION ... Delete ...)
                # The DBConnection context manager handles the transaction start
                delete_query = """
                    DELETE FROM retail_accounting.daily_department_transfers
                    WHERE ddt_id = %s
                """
                try:
                    cur.execute(delete_query, (request_data.ddt_id,))
                except Exception as delete_err:
                    # Equivalent to IF @err <> 0 ROLLBACK
                    logger.error(f"Delete operation failed: {str(delete_err)}")
                    return DepartmentTransferDeleteResponse(
                        return_value=1,
                        error_message="Delete Failed"
                    )

        # 5. COMMIT TRANSACTION happens here via __exit__ of DBConnection
        # If commit fails, an exception would be raised by the context manager.

        # 6. Audit Logging (Equivalent to Insert Into retail_history.audit)
        # This is performed after the main transaction as per the T-SQL logic
        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Construct the comment string: ('Amount - ' + convert(varchar(12), @I_DDT_Cost_Amount) + ', Identity - ' + convert(varchar(10), @DDT_ID)))
                audit_comment = f"Amount - {float(i_ddt_cost_amount or 0):.2f}, Identity - {request_data.ddt_id}"

                audit_query = """
                    INSERT INTO retail_history.audit (
                        tenant_id, a_store, a_date, a_form_type, a_action, 
                        a_creation_date, a_user, a_comment
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                audit_values = (
                    str(request_data.tenant_id),
                    i_ddt_store,
                    i_ddt_date,
                    44,  # Form Type
                    'D',  # Action: Delete
                    datetime.now(),  # getdate()
                    request_data.ddt_user,
                    audit_comment
                )

                cur.execute(audit_query, audit_values)

        # 7. Return Success (Equivalent to Select @Return_Value = 0, Return 0)
        logger.info(f"Successfully deleted transfer ID {request_data.ddt_id} and logged audit.")
        return DepartmentTransferDeleteResponse(
            return_value=0,
            error_message=None
        )

    except Exception as e:
        logger.error(f"Unexpected error in delete_department_transfer: {str(e)}")
        # General error handler to ensure the API returns the expected structure
        return DepartmentTransferDeleteResponse(
            return_value=1,
            error_message=f"System Error: {str(e)}"
        )