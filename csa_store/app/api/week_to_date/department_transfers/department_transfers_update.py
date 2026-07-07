import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter
from psycopg2.extras import RealDictCursor
from app.core.db_utils import DBConnection
from app.schemas.week_to_date.department_transfers.department_transfers_update_schema import DepartmentTransferUpdateRequest, UpdateResponse
from app.utils.week_to_date.department_transfers_helper import calculate_week_ending_date, validate_transfer_date, get_store_config_eow, get_department_description, insert_audit_log




# Configure logging for the application
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/week_to_date/departments_transfers",
    tags=["Week To Date Department Transfers"]
)


@router.put("/update", response_model=UpdateResponse)
def update_department_transfer(request: DepartmentTransferUpdateRequest):
    """
    Update a specified row in the DailyDepartmentTransfers table.
    Equivalent to dbo.csa_DepartmentTransfers_Update stored procedure.
    """
    logger.info(f"Starting update for DDT_ID: {request.ddt_id}")

    # 1. Validation: ID
    if not request.ddt_id:
        return UpdateResponse(return_value=1, error_message="Invalid ID")

    # 2. Validation: Store
    if not request.ddt_store:
        return UpdateResponse(return_value=1, error_message="Invalid Store")

    # 3. Logic: Default To_Store
    ddt_to_store = request.ddt_to_store if request.ddt_to_store is not None else request.ddt_store

    # 4. Logic: Date Calculations (Week Ending Date)
    with DBConnection() as conn:
        with conn.cursor() as cursor:
            sc_eow_last_run = get_store_config_eow(cursor, request.ddt_store)

            if not sc_eow_last_run:
                # If store config not found, we can't proceed with date validation
                return UpdateResponse(return_value=1, error_message="Store Configuration Not Found")

            # Strip time: convert(datetime, convert(varchar(8), @SC_EOW_Last_Run, 1), 1)
            sc_eow_last_run = sc_eow_last_run.replace(hour=0, minute=0, second=0, microsecond=0)

            # SQL DATEPART(weekday) logic: Sunday=1, Monday=2... Saturday=7
            # Python isoweekday(): Monday=1, ..., Sunday=7
            # Map Python to SQL weekday
            sql_weekday = 1 if sc_eow_last_run.isoweekday() == 7 else sc_eow_last_run.isoweekday() + 1

            if sql_weekday == 1:
                week_ending_date = sc_eow_last_run
            else:
                week_ending_date = sc_eow_last_run + timedelta(days=(8 - sql_weekday))

            week_ending_date = week_ending_date.replace(hour=0, minute=0, second=0, microsecond=0)

            # 5. Validation: Date Range
            # If @DDT_Date < dateadd(d, -7, @WeekEndingDate) or @DDT_Date > dateadd(d, 1, @WeekEndingDate)
            if request.ddt_date < (week_ending_date - timedelta(days=7)) or \
                    request.ddt_date > (week_ending_date + timedelta(days=1)):
                return UpdateResponse(return_value=1, error_message="Invalid Date")

            # 6. Validation: User
            if not request.ddt_user or request.ddt_user.strip() == "":
                return UpdateResponse(return_value=1, error_message="Invalid User")

            # 7. Validation: Departments
            if not request.ddt_from_department:
                return UpdateResponse(return_value=1, error_message="Invalid From Department")

            if not request.ddt_to_department:
                return UpdateResponse(return_value=1, error_message="Invalid To Department")

            if request.ddt_from_department == request.ddt_to_department:
                return UpdateResponse(return_value=1, error_message="From & To Department Cannot Be the Same")

            # 8. Validation: Retail and Cost
            if request.ddt_retail_amount is None:
                return UpdateResponse(return_value=1, error_message="Invalid Retail")

            if request.ddt_cost_amount is None:
                return UpdateResponse(return_value=1, error_message="Invalid Cost")

            # 9. Check Existence and Fetch Old Values
            cursor.execute("""
                SELECT DDT_Store, DDT_To_Store, DDT_Date, DDT_From_Department, 
                       DDT_To_Department, DDT_Item_Quantity, DDT_Item_Description, 
                       DDT_User, DDT_Retail_Amount, DDT_Cost_Amount
                FROM retail_accounting.daily_department_transfers
                WHERE DDT_ID = %s
            """, (request.ddt_id,))

            old_row = cursor.fetchone()
            if not old_row:
                return UpdateResponse(return_value=1, error_message="Identity Not Found")

            (old_ddt_store, old_ddt_to_store, old_ddt_date, old_ddt_from_dept,
             old_ddt_to_dept, old_ddt_qty, old_ddt_desc, old_ddt_user,
             old_ddt_retail, old_ddt_cost) = old_row

            # 10. Business Rules
            final_retail_amount = request.ddt_retail_amount
            # If neither department is Grocery (Dept 1), change retail to zero.
            if request.ddt_from_department != 1 and request.ddt_to_department != 1:
                final_retail_amount = Decimal('0.00')

            final_to_store = ddt_to_store
            # If neither department is Independent Store Transfer (Dept 27), Change To_Store value to Store value.
            if request.ddt_from_department != 27 and request.ddt_to_department != 27:
                final_to_store = request.ddt_store

            # 11. Perform Update
            try:
                update_query = """
                    UPDATE retail_accounting.daily_department_transfers
                    SET DDT_To_Store = %s,
                        DDT_Date = %s,
                        DDT_From_Department = %s,
                        DDT_To_Department = %s,
                        DDT_Item_Quantity = %s,
                        DDT_Item_Description = %s,
                        DDT_User = %s,
                        DDT_Retail_Amount = %s,
                        DDT_Cost_Amount = %s
                    WHERE DDT_ID = %s
                """
                cursor.execute(update_query, (
                    final_to_store,
                    request.ddt_date,
                    request.ddt_from_department,
                    request.ddt_to_department,
                    request.ddt_item_quantity,
                    request.ddt_item_description,
                    request.ddt_user,
                    final_retail_amount,
                    request.ddt_cost_amount,
                    request.ddt_id
                ))
            except Exception as e:
                logger.error(f"Update failed: {str(e)}")
                return UpdateResponse(return_value=1, error_message="Insert Failed")

            # 12. Audit Logging
            # Date Audit
            if old_ddt_date != request.ddt_date:
                msg = f"Date Changed From: {old_ddt_date.strftime('%m/%d/%y')} To: {request.ddt_date.strftime('%m/%d/%y')}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # To Store Audit
            if old_ddt_to_store != final_to_store:
                msg = f"To Store Changed From: {old_ddt_to_store} To: {final_to_store}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # From Department Audit
            if old_ddt_from_dept != request.ddt_from_department:
                new_desc = get_department_description(cursor, request.ddt_from_department,
                                                      "retail_accounting.departments")
                old_desc = get_department_description(cursor, old_ddt_from_dept, 'retail_accounting.departments')
                msg = f"From Department Changed From: {old_desc} To: {new_desc}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # To Department Audit
            if old_ddt_to_dept != request.ddt_to_department:
                new_desc = get_department_description(cursor, request.ddt_to_department,
                                                      "retail_accounting.departments")
                old_desc = get_department_description(cursor, old_ddt_to_dept, "retail_accounting.departments")
                msg = f"To Department Changed From: {old_desc} To: {new_desc}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # Quantity Audit
            if old_ddt_qty != request.ddt_item_quantity:
                msg = f"Item Quantity Changed From: {old_ddt_qty} To: {request.ddt_item_quantity}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # Description Audit
            if old_ddt_desc != request.ddt_item_description:
                msg = f"Item Description Changed From: {old_ddt_desc} To: {request.ddt_item_description}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # User Audit
            if old_ddt_user != request.ddt_user:
                msg = f"User Changed From: {old_ddt_user} To: {request.ddt_user}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # Retail Amount Audit
            if old_ddt_retail != final_retail_amount:
                msg = f"Retail Amount Changed From: {old_ddt_retail} To: {final_retail_amount}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

            # Cost Amount Audit
            if old_ddt_cost != request.ddt_cost_amount:
                msg = f"Cost Amount Changed From: {old_ddt_cost} To: {request.ddt_cost_amount}"
                insert_audit_log(cursor, str(request.tenant_id), request.ddt_store, request.ddt_date, request.ddt_user, msg)

    return UpdateResponse(return_value=0)