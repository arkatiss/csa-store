from datetime import date, timedelta

def get_sql_weekday(dt: date) -> int:
    """
    Returns SQL Server style weekday where Sunday = 1, Saturday = 7.
    """
    return (dt.isoweekday() % 7) + 1

def get_week_ending_date(sc_eow_last_run: date) -> date:
    """
    Calculates the Week Ending Date. If it's Sunday, it's the same day. 
    Otherwise it's the next Sunday.
    """
    weekday = get_sql_weekday(sc_eow_last_run)
    if weekday == 1:
        return sc_eow_last_run
    else:
        return sc_eow_last_run + timedelta(days=(8 - weekday))

def is_valid_date(def_date: date, week_ending_date: date) -> bool:
    """
    Valid dates are between WeekEndingDate - 6 days and WeekEndingDate.
    """
    start_date = week_ending_date - timedelta(days=6)
    return start_date <= def_date <= week_ending_date

def is_store_open(sc_open_days: str, def_date: date) -> bool:
    """
    sc_open_days is a string of active SQL weekdays (e.g. "1234567").
    """
    if sc_open_days is None:
        return False
    weekday_str = str(get_sql_weekday(def_date))
    return weekday_str in sc_open_days

def update_dsc_with_form102(cur, tenant_id: str, store: int, week_ending_date: date, sc_eod_last_run: date):
    """
    Updates retail.daily_sales_cash_total with Previous and Actual Deposits.
    Equivalent to csa_UpdateDSCWithForm102.
    """
    # 1. Update DSCT_Previous_Deposits
    cur.execute("""
        SELECT COALESCE(SUM(DEF_Amount_2), 0)
        FROM retail_accounting.data_entry_forms
        WHERE tenant_id = %s 
          AND def_store = %s 
          AND def_form_type = 1 
          AND def_date < %s
    """, (tenant_id, store, sc_eod_last_run))
    previous_deposits = cur.fetchone()[0]

    cur.execute("""
        UPDATE retail.daily_sales_cash_total
        SET dsct_previous_deposits = %s
        WHERE tenant_id = %s 
          AND dsct_store = %s 
          AND dsct_week_ending_date = %s
    """, (previous_deposits, tenant_id, store, week_ending_date))

    # 2. Update DSCT_Actual_Daily_Deposits
    cur.execute("""
        SELECT COALESCE(SUM(DEF_Amount_2), 0)
        FROM retail_accounting.data_entry_forms
        WHERE tenant_id = %s 
          AND def_store = %s 
          AND def_form_type = 1 
          AND def_date >= %s
    """, (tenant_id, store, sc_eod_last_run))
    actual_deposits = cur.fetchone()[0]

    cur.execute("""
        UPDATE retail.daily_sales_cash_total
        SET dsct_actual_daily_deposits = %s
        WHERE tenant_id = %s 
          AND dsct_store = %s 
          AND dsct_week_ending_date = %s
    """, (actual_deposits, tenant_id, store, week_ending_date))
