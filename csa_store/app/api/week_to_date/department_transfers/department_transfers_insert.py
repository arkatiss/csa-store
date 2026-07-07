import os
import logging
from datetime import datetime
from fastapi import APIRouter
from psycopg2.extras import RealDictCursor
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.department_transfers.department_transfers_insert_schema import DepartmentTransferRequest, DepartmentTransferResponse
from app.utils.week_to_date.department_transfers_helper import calculate_week_ending_date, validate_transfer_date




# Configure logging for the application
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/week_to_date/departments_transfers",
    tags=["Week To Date Department Transfers"]
)


@router.post("/insert", response_model=DepartmentTransferResponse)
async def insert_department_transfer(request: DepartmentTransferRequest):
    """
    Main API logic for csa_DepartmentTransfers_Insert.
    Performs validation, date calculation, and inserts records into
    daily_department_transfers and audit tables.
    """
    logger.info(f"Starting csa_DepartmentTransfers_Insert for Store: {request.ddt_store}")

    # 1. Validate Store
    if not request.ddt_store:
        logger.warning("Invalid Store provided")
        return DepartmentTransferResponse(return_value=1, error_message="Invalid Store")

    # 2. Validate To Store
    if not request.ddt_to_store:
        logger.warning("Invalid To Store provided")
        return DepartmentTransferResponse(return_value=1, error_message="Invalid To Store")

    try:
        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 3. Fetch Store Configuration
                # Select @SC_EOW_Last_Run = SC_EOW_Last_Run, @SC_EOD_Last_Run = SC_EOD_Last_Run
                # From retail_accounting.store_configuration with (nolock) Where SC_Store = @DDT_Store
                cur.execute(
                    """
                    SELECT SC_EOW_Last_Run, SC_EOD_Last_Run 
                    FROM retail_accounting.store_configuration 
                    WHERE SC_Store = %s
                    """,
                    (request.ddt_store,)
                )
                config_row = cur.fetchone()

                if not config_row:
                    logger.error(f"Store configuration not found for store {request.ddt_store}")
                    return DepartmentTransferResponse(return_value=1, error_message="Store Configuration Not Found")

                sc_eow_last_run, sc_eod_last_run = config_row

                # 4. Calculate WeekEndingDate (Logic moved to helper for clarity)
                week_ending_date = calculate_week_ending_date(sc_eow_last_run)

                # 5. Validate Transfer Date
                # If @DDT_Date < dateadd(d, -7, @WeekEndingDate) or @DDT_Date > dateadd(d, 1, @WeekEndingDate)
                if not validate_transfer_date(request.ddt_date, week_ending_date):
                    logger.warning(f"Invalid Date: {request.ddt_date} for Week Ending: {week_ending_date}")
                    return DepartmentTransferResponse(return_value=1, error_message="Invalid Date")

                # 6. Validate User
                if not request.ddt_user or request.ddt_user.strip() == "":
                    logger.warning("Invalid User provided")
                    return DepartmentTransferResponse(return_value=1, error_message="Invalid User")

                # 7. Validate From Department
                if not request.ddt_from_department:
                    logger.warning("Invalid From Department provided")
                    return DepartmentTransferResponse(return_value=1, error_message="Invalid From Department")

                # 8. Validate To Department
                if not request.ddt_to_department:
                    logger.warning("Invalid To Department provided")
                    return DepartmentTransferResponse(return_value=1, error_message="Invalid To Department")

                # 9. Validate From & To Departments are not the same
                if request.ddt_from_department == request.ddt_to_department:
                    logger.warning("From & To Departments are the same")
                    return DepartmentTransferResponse(
                        return_value=1,
                        error_message="From & To Departments Cannot Be The Same"
                    )

                # 10. Validate Retail Amount (Pydantic handles basic type, but we check existence)
                if request.ddt_retail_amount is None:
                    logger.warning("Invalid Retail Amount")
                    return DepartmentTransferResponse(return_value=1, error_message="Invalid Retail Amount")

                # 11. Validate Cost Amount
                if request.ddt_cost_amount is None:
                    logger.warning("Invalid Cost Amount")
                    return DepartmentTransferResponse(return_value=1, error_message="Invalid Cost Amount")

                # 12. Insert into daily_department_transfers
                # BEGIN TRANSACTION is handled by DBConnection context manager
                try:
                    insert_query = """
                        INSERT INTO retail_accounting.daily_department_transfers (
                            tenant_id, ddt_store, ddt_to_store, ddt_date, ddt_from_department,
                            ddt_to_department, ddt_item_quantity, ddt_item_description,
                            ddt_user, ddt_retail_amount, ddt_cost_amount, ddt_retail_acct_update_flag
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING ddt_id;
                    """
                    # Note: In Postgres, we use RETURNING to get the identity (@@IDENTITY)
                    cur.execute(insert_query, (
                        str(request.tenant_id),
                        request.ddt_store,
                        request.ddt_to_store,
                        request.ddt_date,
                        request.ddt_from_department,
                        request.ddt_to_department,
                        request.ddt_item_quantity,
                        request.ddt_item_description,
                        request.ddt_user,
                        request.ddt_retail_amount,
                        request.ddt_cost_amount,
                        "Y"
                    ))

                    new_id = cur.fetchone()[0]
                    logger.info(f"Successfully inserted transfer record. ID: {new_id}")

                except Exception as e:
                    # ROLLBACK is handled by DBConnection __exit__ on exception
                    logger.error(f"Insert Failed: {str(e)}")
                    return DepartmentTransferResponse(return_value=1, error_message="Insert Failed")

                # 13. Insert into Audit Table
                # Values (@DDT_Store, @DDT_Date, 44, 'I', getdate(), @DDT_User,
                # ('Amount - ' + convert(varchar(12), @DDT_Cost_Amount) + ', Identity - ' + convert(varchar(10), @ID)))
                try:
                    audit_description = f"Amount - {request.ddt_cost_amount:.2f}, Identity - {new_id}"
                    audit_query = """
                        INSERT INTO retail_history.audit (
                            tenant_id, a_store, a_date, a_form_type, a_action,
                            a_creation_date, a_user, a_comment
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cur.execute(audit_query, (
                        str(request.tenant_id),
                        request.ddt_store,
                        request.ddt_date,
                        44,
                        'I',
                        datetime.now(),
                        request.ddt_user,
                        audit_description
                    ))
                    logger.info("Audit record inserted successfully")

                except Exception as e:
                    # If audit fails, we still return failure as per standard transactional integrity
                    logger.error(f"Audit Insert Failed: {str(e)}")
                    return DepartmentTransferResponse(return_value=1, error_message="Audit Failed")

                # COMMIT TRANSACTION is handled by DBConnection __exit__
                return DepartmentTransferResponse(
                    return_value=0,
                    error_message="",
                    id=new_id
                )

    except Exception as e:
        logger.critical(f"Unexpected error in API: {str(e)}")
        return DepartmentTransferResponse(return_value=1, error_message=f"System Error: {str(e)}")