import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily_taxes_input_ind_only.daily_taxes_manual_update_schema import DailyTaxesManualUpdateRequest, DailyTaxesManualUpdateResponse
from app.utils.form102_helper import get_week_ending_date

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily_taxes_input_ind_only",
    tags=["Daily Taxes Input Ind Only"]
)

@router.put("/manual_update", response_model=DailyTaxesManualUpdateResponse)
def csa_daily_taxes_manual_update(request: DailyTaxesManualUpdateRequest):
    """
    Equivalent of:
    csa_DailyTaxes_Manual_Update
    """
    try:
        # Initial Validations
        if request.dtm_store is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid Store")
        if request.dtm_file_date is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid Date")
        if not request.user or str(request.user).strip() == '':
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid User")

        if request.dtm_net_sales1 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid Net Sales for tax Rate 1")
        if request.dtm_net_sales2 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid Net Sales for tax Rate 2")
        if request.dtm_net_sales3 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid Net Sales for tax Rate 3")
        if request.dtm_net_sales4 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid Net Sales for tax Rate 4")
            
        if request.dtm_sales_tax_collected1 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid  Sales Tax Collected for tax Rate 1")
        if request.dtm_sales_tax_collected2 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid  Sales Tax Collected for tax Rate 2")
        if request.dtm_sales_tax_collected3 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid  Sales Tax Collected for tax Rate 3")
        if request.dtm_sales_tax_collected4 is None:
            return DailyTaxesManualUpdateResponse(return_value=1, error_message="Invalid  Sales Tax Collected for tax Rate 4")

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Get Week Ending Date
                week_ending_date = get_week_ending_date(cur, request.dtm_store)
                if not week_ending_date:
                    return DailyTaxesManualUpdateResponse(return_value=1, error_message="Could not determine week ending date")

                # Check if rows exist
                cur.execute("""
                    SELECT count(*)
                    FROM retail_history.daily_taxes_manual
                    WHERE dtm_store = %s AND dtm_file_date = %s
                """, (request.dtm_store, request.dtm_file_date))
                count_record = cur.fetchone()
                
                if not count_record or count_record[0] == 0:
                    return DailyTaxesManualUpdateResponse(return_value=1, error_message="Row Not Found")

                # Fetch Old Values
                cur.execute("""
                    SELECT dtm_tax_rate, dtm_net_sales, dtm_sales_tax_collected
                    FROM retail_history.daily_taxes_manual
                    WHERE dtm_store = %s AND dtm_file_date = %s
                """, (request.dtm_store, request.dtm_file_date))
                
                old_rows = cur.fetchall()
                old_net_sales = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0}
                old_tax_collected = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0}
                
                for r in old_rows:
                    rate = str(r[0]).strip()
                    if rate in old_net_sales:
                        old_net_sales[rate] = float(r[1]) if r[1] is not None else 0.0
                        old_tax_collected[rate] = float(r[2]) if r[2] is not None else 0.0

                try:
                    # Update DailyTaxes_Manual for each tax rate
                    update_data = [
                        (request.dtm_net_sales1, request.dtm_sales_tax_collected1, request.dtm_store, request.dtm_file_date, '1'),
                        (request.dtm_net_sales2, request.dtm_sales_tax_collected2, request.dtm_store, request.dtm_file_date, '2'),
                        (request.dtm_net_sales3, request.dtm_sales_tax_collected3, request.dtm_store, request.dtm_file_date, '3'),
                        (request.dtm_net_sales4, request.dtm_sales_tax_collected4, request.dtm_store, request.dtm_file_date, '4')
                    ]
                    
                    cur.executemany("""
                        UPDATE retail_history.daily_taxes_manual
                        SET dtm_net_sales = %s,
                            dtm_sales_tax_collected = %s
                        WHERE dtm_store = %s AND dtm_file_date = %s AND dtm_tax_rate = %s
                    """, update_data)

                    # Update WTD Taxes Manual
                    cur.execute("""
                        UPDATE retail_accounting_original.wtd_taxes_manual AS wtm
                        SET wtm_net_sales = q1.net_sales,
                            wtm_sales_tax_collected = q1.sales_tax_collected
                        FROM (
                            SELECT dtm_store, dtm_tax_rate, 
                                   SUM(dtm_net_sales) AS net_sales, 
                                   SUM(dtm_sales_tax_collected) AS sales_tax_collected
                            FROM retail_history.daily_taxes_manual
                            GROUP BY dtm_store, dtm_tax_rate
                            HAVING dtm_store = %s
                        ) AS q1
                        WHERE wtm.wtm_store = q1.dtm_store
                          AND wtm.wtm_tax_rate = q1.dtm_tax_rate
                          AND wtm.wtm_store = %s
                          AND wtm.wtm_week_ending_date = %s
                    """, (request.dtm_store, request.dtm_store, week_ending_date))

                    # Update Daily Taxes for each tax rate
                    dt_updates = [
                        (request.dtm_net_sales1, request.dtm_sales_tax_collected1, request.dtm_net_sales1, '1', request.dtm_store, request.dtm_file_date, '1'),
                        (request.dtm_net_sales2, request.dtm_sales_tax_collected2, request.dtm_net_sales2, '2', request.dtm_store, request.dtm_file_date, '2'),
                        (request.dtm_net_sales3, request.dtm_sales_tax_collected3, request.dtm_net_sales3, '3', request.dtm_store, request.dtm_file_date, '3'),
                        (request.dtm_net_sales4, request.dtm_sales_tax_collected4, request.dtm_net_sales4, '4', request.dtm_store, request.dtm_file_date, '4')
                    ]
                    
                    # Since Postgres UPDATE with JOIN differs slightly from T-SQL, we format it as:
                    for i in range(1, 5):
                        rate = str(i)
                        net_sales = getattr(request, f"dtm_net_sales{i}")
                        tax_collected = getattr(request, f"dtm_sales_tax_collected{i}")
                        
                        cur.execute(f"""
                            UPDATE retail_history.daily_taxes AS dt
                            SET dt_net_sales = (%s + p.pos_daily_net_sales_rate_{i}),
                                dt_sales_tax_collected = (%s + p.pos_daily_sales_tax_collected_rate_{i}),
                                dt_sales_tax_liability = (%s + p.pos_daily_net_sales_rate_{i}) * sc.sc_tax_rate_{i}
                            FROM retail_history.pos AS p
                            INNER JOIN retail_accounting.store_configuration AS sc ON p.pos_store = sc.sc_store
                            WHERE dt.dt_store = p.pos_store 
                              AND dt.dt_file_date = p.pos_file_date
                              AND p.pos_store = %s 
                              AND p.pos_file_date = %s 
                              AND dt.dt_tax_rate = %s
                        """, (net_sales, tax_collected, net_sales, request.dtm_store, request.dtm_file_date, rate))

                    # Update WTD Taxes
                    cur.execute("""
                        UPDATE retail_accounting_original.wtd_taxes AS wt
                        SET wt_net_sales = q1.net_sales,
                            wt_sales_tax_collected = q1.sales_tax_collected,
                            wt_sales_tax_liability = q1.sales_tax_liability
                        FROM (
                            SELECT dt_store, dt_tax_rate,
                                   SUM(dt_net_sales) AS net_sales,
                                   SUM(dt_sales_tax_collected) AS sales_tax_collected,
                                   SUM(dt_sales_tax_liability) AS sales_tax_liability
                            FROM retail_history.daily_taxes
                            GROUP BY dt_store, dt_tax_rate
                            HAVING dt_store = %s
                        ) AS q1
                        WHERE wt.wt_store = q1.dt_store
                          AND wt.wt_tax_rate = q1.dt_tax_rate
                          AND wt.wt_store = %s
                          AND wt.wt_week_ending_date = %s
                    """, (request.dtm_store, request.dtm_store, week_ending_date))

                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    logger.exception("Transaction Failed in DailyTaxes_Manual_Update")
                    return DailyTaxesManualUpdateResponse(return_value=1, error_message="Commit Failed")

                # Insert Audit Logs
                audit_records = []
                # Net Sales
                if old_net_sales['1'] != request.dtm_net_sales1:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Net Sales for Tax Rate 1  Changed From - {old_net_sales['1']} To - {request.dtm_net_sales1}"))
                if old_net_sales['2'] != request.dtm_net_sales2:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Net Sales for Tax Rate 2  Changed From - {old_net_sales['2']} To - {request.dtm_net_sales2}"))
                if old_net_sales['3'] != request.dtm_net_sales3:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Net Sales for Tax Rate 3  Changed From - {old_net_sales['3']} To - {request.dtm_net_sales3}"))
                if old_net_sales['4'] != request.dtm_net_sales4:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Net Sales for Tax Rate 4  Changed From - {old_net_sales['4']} To - {request.dtm_net_sales4}"))
                
                # Sales Tax Collected
                if old_tax_collected['1'] != request.dtm_sales_tax_collected1:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Sales tax Collected for Tax Rate 1  Changed From - {old_tax_collected['1']} To - {request.dtm_sales_tax_collected1}"))
                if old_tax_collected['2'] != request.dtm_sales_tax_collected2:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Sales tax Collected for Tax Rate 2  Changed From - {old_tax_collected['2']} To - {request.dtm_sales_tax_collected2}"))
                if old_tax_collected['3'] != request.dtm_sales_tax_collected3:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Sales tax Collected for Tax Rate 3  Changed From - {old_tax_collected['3']} To - {request.dtm_sales_tax_collected3}"))
                if old_tax_collected['4'] != request.dtm_sales_tax_collected4:
                    audit_records.append((request.tenant_id, request.dtm_store, request.dtm_file_date, 19, 'U', request.user, f"Sales tax Collected for Tax Rate 4  Changed From - {old_tax_collected['4']} To - {request.dtm_sales_tax_collected4}"))

                if audit_records:
                    cur.executemany("""
                        INSERT INTO retail_history.audit
                        (tenant_id, a_store, a_date, a_form_type, a_action, a_creation_date, a_user, a_comment)
                        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
                    """, audit_records)
                    conn.commit()

                return DailyTaxesManualUpdateResponse(return_value=0, error_message="")

    except Exception as ex:
        logger.exception("Error in DailyTaxes_Manual_Update")
        return DailyTaxesManualUpdateResponse(
            return_value=1,
            error_message="Update DailyTaxes (Manual) Failed"
        )
