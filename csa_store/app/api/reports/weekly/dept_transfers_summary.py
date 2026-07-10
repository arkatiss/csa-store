import logging
from fastapi import APIRouter
from decimal import Decimal
from datetime import datetime
from app.core.db_utils import DBConnection
from app.schemas.reports.weekly.dept_transfers_summary_schema import (
    DeptTransfersSummaryRequest,
    DeptTransfersSummaryResponse,
    DeptTransfersSummaryItem
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports/weekly",
    tags=["Reports Weekly Dept Transfers Summary"]
)

@router.post("/dept_transfers_summary", response_model=DeptTransfersSummaryResponse)
def csa_department_transfers_dept_summary(request: DeptTransfersSummaryRequest):
    try:
        if request.store is None or str(request.store).strip() == '':
            return DeptTransfersSummaryResponse(return_value=1, error_message="Invalid Store", data=None)

        store = request.store
        week_end = request.week_ending_date
        
        with DBConnection() as conn:
            with conn.cursor() as cur:
                # 1. Total Retail Credits
                cur.execute("""
                    SELECT SUM(DDT_Retail_Amount) * -1
                    FROM retail_accounting.daily_department_transfers
                    WHERE DDT_Store = %s AND DDT_From_Department = 1
                """, (store,))
                row = cur.fetchone()
                total_retail_credits = row[0] if row and row[0] is not None else Decimal('0.0')

                # 2. Total Retail Charges
                cur.execute("""
                    SELECT SUM(DDT_Retail_Amount)
                    FROM retail_accounting.daily_department_transfers
                    WHERE DDT_Store = %s AND DDT_To_Department = 1
                """, (store,))
                row = cur.fetchone()
                total_retail_charges = row[0] if row and row[0] is not None else Decimal('0.0')

                # 3. InterStore Count
                cur.execute("""
                    SELECT COUNT(*)
                    FROM retail_accounting.daily_department_transfers
                    WHERE DDT_Store = %s AND (DDT_From_Department = 27 OR DDT_To_Department = 27)
                """, (store,))
                row = cur.fetchone()
                interstore_count = row[0] if row and row[0] is not None else 0

                data = []
                def add_row(dept, desc, retail, r_type, cost, c_type):
                    data.append(DeptTransfersSummaryItem(
                        store=store,
                        department=dept,
                        description=desc,
                        retail=str(retail) if retail != '' else '',
                        retail_type=r_type,
                        cost=str(cost) if cost != '' else '',
                        cost_type=c_type
                    ))
                
                # Headers
                add_row(0, 'Transfers Summary By Department', '', 'B', '', 'B')
                add_row(0, f'Store: {store}', '', 'B', '', 'B')
                add_row(0, f'Wk Ending Date: {week_end.strftime("%m/%d/%y") if week_end else ""}', '', 'B', '', 'B')
                add_row(0, ' ', '', 'B', '', 'B')
                add_row(0, 'CREDITS', 'RETAIL', 'H', 'COST', 'H')
                add_row(0, '------------------', '---------------', 'H', '---------------', 'H')
                
                # Credits by department
                cur.execute("""
                    SELECT DDT_From_Department, D_Description,
                        SUM(CASE WHEN DDT_From_Department = 1 THEN DDT_Retail_Amount ELSE 0 END) * -1,
                        SUM(DDT_Cost_Amount) * -1
                    FROM retail_accounting.daily_department_transfers
                    LEFT OUTER JOIN retail_accounting.departments ON DDT_From_Department = D_ID
                    WHERE DDT_Store = %s AND (DDT_From_Department <> 1 OR DDT_To_Department NOT IN (23, 48))
                    GROUP BY DDT_Store, DDT_From_Department, D_Description
                """, (store,))
                for r in cur.fetchall():
                    add_row(r[0] or 0, r[1] or '', r[2] if r[2] is not None else 0, 'M', r[3] if r[3] is not None else 0, 'M')

                # Grocery to Reclamation
                cur.execute("""
                    SELECT DDT_From_Department,
                        SUM(DDT_Retail_Amount) * -1,
                        SUM(DDT_Cost_Amount) * -1
                    FROM retail_accounting.daily_department_transfers
                    WHERE DDT_Store = %s AND (DDT_From_Department = 1 AND DDT_To_Department = 23)
                    GROUP BY DDT_Store, DDT_From_Department
                """, (store,))
                for r in cur.fetchall():
                    add_row(r[0] or 0, 'Grocery Reclamation', r[1] if r[1] is not None else 0, 'M', r[2] if r[2] is not None else 0, 'M')

                # Grocery to Continuity
                cur.execute("""
                    SELECT DDT_From_Department,
                        SUM(DDT_Retail_Amount) * -1,
                        SUM(DDT_Cost_Amount) * -1
                    FROM retail_accounting.daily_department_transfers
                    WHERE DDT_Store = %s AND (DDT_From_Department = 1 AND DDT_To_Department = 48)
                    GROUP BY DDT_Store, DDT_From_Department
                """, (store,))
                for r in cur.fetchall():
                    add_row(r[0] or 0, 'Grocery Continuity', r[1] if r[1] is not None else 0, 'M', r[2] if r[2] is not None else 0, 'M')
                
                add_row(0, '------------------', '---------------', 'H', '---------------', 'H')
                
                # Total Credits
                cur.execute("""
                    SELECT SUM(DDT_Cost_Amount) * -1
                    FROM retail_accounting.daily_department_transfers
                    WHERE DDT_Store = %s
                """, (store,))
                tc_row = cur.fetchone()
                total_cost_credits = tc_row[0] if tc_row and tc_row[0] is not None else Decimal('0.0')
                add_row(0, 'TOTAL CREDITS', total_retail_credits, 'M', total_cost_credits, 'M')

                add_row(0, ' ', '', 'B', '', 'B')
                add_row(0, 'CHARGES', 'RETAIL', 'H', 'COST', 'H')
                add_row(0, '------------------', '---------------', 'H', '---------------', 'H')

                # Charges by department
                cur.execute("""
                    SELECT DDT_To_Department, D_Description,
                        SUM(CASE WHEN DDT_To_Department = 1 THEN DDT_Retail_Amount ELSE 0 END),
                        SUM(DDT_Cost_Amount)
                    FROM retail_accounting.daily_department_transfers
                    LEFT OUTER JOIN retail_accounting.departments ON DDT_To_Department = D_ID
                    WHERE DDT_Store = %s
                    GROUP BY DDT_Store, DDT_To_Department, D_Description
                """, (store,))
                for r in cur.fetchall():
                    add_row(r[0] or 0, r[1] or '', r[2] if r[2] is not None else 0, 'M', r[3] if r[3] is not None else 0, 'M')

                add_row(0, '------------------', '---------------', 'H', '---------------', 'H')

                # Total Charges
                cur.execute("""
                    SELECT SUM(DDT_Cost_Amount)
                    FROM retail_accounting.daily_department_transfers
                    WHERE DDT_Store = %s
                """, (store,))
                tc_row = cur.fetchone()
                total_cost_charges = tc_row[0] if tc_row and tc_row[0] is not None else Decimal('0.0')
                add_row(0, 'TOTAL CHARGES', total_retail_charges, 'M', total_cost_charges, 'M')

                add_row(0, ' ', '', 'B', '', 'B')
                add_row(0, '==================', '===============', 'H', '===============', 'H')
                add_row(0, ' ', '', 'B', '', 'B')
                add_row(0, ' ', '', 'B', '', 'B')
                add_row(0, 'Net Transfer Per Department Weekly Report', '', 'B', '', 'B')
                add_row(0, ' ', '', 'B', '', 'B')
                add_row(0, 'DEPARTMENT', 'RETAIL', 'H', 'COST', 'H')
                add_row(0, '------------------', '---------------', 'H', '---------------', 'H')

                # Net Transfers
                cur.execute("""
                    SELECT Department, Description, SUM(Retail), SUM(Cost)
                    FROM (
                        SELECT DDT_From_Department as Department, D_Description as Description,
                            SUM(CASE WHEN DDT_From_Department = 1 THEN DDT_Retail_Amount ELSE 0 END) * -1 as Retail,
                            SUM(DDT_Cost_Amount) * -1 as Cost
                        FROM retail_accounting.daily_department_transfers
                        LEFT OUTER JOIN retail_accounting.departments ON DDT_From_Department = D_ID
                        WHERE DDT_Store = %s AND (DDT_From_Department <> 1 OR DDT_To_Department NOT IN (23, 48))
                        GROUP BY DDT_Store, DDT_From_Department, D_Description
                        UNION ALL
                        SELECT DDT_From_Department as Department, 'Grocery Reclamation' as Description,
                            SUM(DDT_Retail_Amount) * -1 as Retail,
                            SUM(DDT_Cost_Amount) * -1 as Cost
                        FROM retail_accounting.daily_department_transfers
                        WHERE DDT_Store = %s AND (DDT_From_Department = 1 AND DDT_To_Department = 23)
                        GROUP BY DDT_Store, DDT_From_Department
                        UNION ALL
                        SELECT DDT_From_Department as Department, 'Grocery Continuity' as Description,
                            SUM(DDT_Retail_Amount) * -1 as Retail,
                            SUM(DDT_Cost_Amount) * -1 as Cost
                        FROM retail_accounting.daily_department_transfers
                        WHERE DDT_Store = %s AND (DDT_From_Department = 1 AND DDT_To_Department = 48)
                        GROUP BY DDT_Store, DDT_From_Department
                        UNION ALL
                        SELECT DDT_To_Department as Department, D_Description as Description,
                            SUM(CASE WHEN DDT_To_Department = 1 THEN DDT_Retail_Amount ELSE 0 END) as Retail,
                            SUM(DDT_Cost_Amount) as Cost
                        FROM retail_accounting.daily_department_transfers
                        LEFT OUTER JOIN retail_accounting.departments ON DDT_To_Department = D_ID
                        WHERE DDT_Store = %s
                        GROUP BY DDT_Store, DDT_To_Department, D_Description
                    ) as query1
                    GROUP BY Department, Description
                """, (store, store, store, store))
                for r in cur.fetchall():
                    add_row(r[0] or 0, r[1] or '', r[2] if r[2] is not None else 0, 'M', r[3] if r[3] is not None else 0, 'M')

                if interstore_count > 0:
                    add_row(0, '==================', '===============', 'H', '===============', 'H')
                    add_row(0, ' ', '', 'B', '', 'B')
                    add_row(0, 'Inter-Store Transfer Summary', '', 'B', '', 'B')
                    add_row(0, ' ', '', 'B', '', 'B')
                    add_row(0, 'CREDITS FROM STORE', '', 'B', 'COST', 'H')
                    add_row(0, '------------------', '---------------', 'H', '---------------', 'H')
                    
                    cur.execute("""
                        SELECT 'Store ' || CAST(DDT_To_Store AS VARCHAR(10)),
                               SUM(DDT_Cost_Amount)
                        FROM retail_accounting.daily_department_transfers
                        WHERE DDT_Store = %s AND DDT_To_Department = 27
                        GROUP BY DDT_Store, DDT_To_Store
                    """, (store,))
                    for r in cur.fetchall():
                        add_row(0, r[0] or '', 0, 'M', r[1] if r[1] is not None else 0, 'M')

                    add_row(0, ' ', '', 'B', '', 'B')
                    add_row(0, 'CHARGES TO STORE', '', 'B', 'COST', 'H')
                    add_row(0, '------------------', '---------------', 'H', '---------------', 'H')
                    
                    cur.execute("""
                        SELECT 'Store ' || CAST(DDT_To_Store AS VARCHAR(10)),
                               SUM(DDT_Cost_Amount) * -1
                        FROM retail_accounting.daily_department_transfers
                        WHERE DDT_Store = %s AND DDT_From_Department = 27
                        GROUP BY DDT_Store, DDT_To_Store
                    """, (store,))
                    for r in cur.fetchall():
                        add_row(0, r[0] or '', 0, 'M', r[1] if r[1] is not None else 0, 'M')

                return DeptTransfersSummaryResponse(return_value=0, error_message="", data=data)

    except Exception as ex:
        logger.exception("Error in csa_DepartmentTransfers_DeptSummary")
        return DeptTransfersSummaryResponse(return_value=1, error_message="Select Failed", data=None)
