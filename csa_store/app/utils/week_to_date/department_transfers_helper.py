import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def calculate_week_ending_date(sc_eow_last_run: datetime) -> datetime:
    """
    Replicates the T-SQL logic for calculating the WeekEndingDate.
    SQL Logic:
    If DatePart(weekday, @SC_EOW_Last_Run) = 1 (Sunday)
        WeekEndingDate = SC_EOW_Last_Run
    Else
        WeekEndingDate = SC_EOW_Last_Run + (8 - datepart(weekday, SC_EOW_Last_Run))

    Python datetime.isoweekday(): Monday=1, ..., Sunday=7.
    SQL Server default DATEFIRST 7: Sunday=1, Monday=2, ..., Saturday=7.
    """
    # Normalize to date only (equivalent to convert(varchar(8), ..., 1))
    base_date = sc_eow_last_run.replace(hour=0, minute=0, second=0, microsecond=0)

    # SQL weekday 1 is Sunday. Python isoweekday 7 is Sunday.
    # We map SQL weekday to Python logic.
    # SQL: 1(Sun), 2(Mon), 3(Tue), 4(Wed), 5(Thu), 6(Fri), 7(Sat)
    sql_weekday = base_date.isoweekday() % 7 + 1

    if sql_weekday == 1:
        week_ending_date = base_date
    else:
        days_to_add = 8 - sql_weekday
        week_ending_date = base_date + timedelta(days=days_to_add)

    return week_ending_date.replace(hour=0, minute=0, second=0, microsecond=0)


def validate_transfer_date(ddt_date: datetime, week_ending_date: datetime) -> bool:
    """
    Replicates the T-SQL logic:
    If @DDT_Date < dateadd(d, -7, @WeekEndingDate) or @DDT_Date > dateadd(d, 1, @WeekEndingDate)
    """
    ddt_date_only = ddt_date.replace(hour=0, minute=0, second=0, microsecond=0)
    lower_bound = week_ending_date - timedelta(days=7)
    upper_bound = week_ending_date + timedelta(days=1)

    if ddt_date_only < lower_bound or ddt_date_only > upper_bound:
        return False
    return True


def get_store_config_eow(cursor, store_id: int) -> Optional[datetime]:
    """Fetches the SC_EOW_Last_Run for a specific store."""
    query = """
        SELECT SC_EOW_Last_Run 
        FROM retail_accounting.store_configuration 
        WHERE SC_Store = %s
    """
    cursor.execute(query, (store_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_department_description(cursor, dept_id: int, schema_table: str) -> str:
    """Fetches department description from specified table."""
    query = f"SELECT D_Description FROM {schema_table} WHERE D_ID = %s"
    cursor.execute(query, (dept_id,))
    result = cursor.fetchone()
    return result[0] if result else ""

def insert_audit_log(cursor, tenant_id, store: int, date: datetime, user: str, message: str):
    """Inserts a record into the audit table."""
    query = """
        INSERT INTO retail_history.audit (
            tenant_id, a_store, a_date, a_form_type, a_action, a_creation_date, a_user, a_comment
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (str(tenant_id), store, date, 44, 'U', datetime.now(), user, message))