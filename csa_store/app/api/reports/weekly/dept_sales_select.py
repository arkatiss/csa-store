import logging
from fastapi import APIRouter
from datetime import timedelta
from decimal import Decimal
from app.core.db_utils import DBConnection
from app.schemas.reports.weekly.dept_sales_select_schema import DeptSalesSelectRequest, DeptSalesSelectResponse, \
    DeptSalesSelectItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports/weekly",
    tags=["Reports Weekly Dept Sales"]
)


@router.post("/dept_sales_select", response_model=DeptSalesSelectResponse)
def csa_dept_sales_select(request: DeptSalesSelectRequest):
    try:
        if request.store is None or str(request.store).strip() == '':
            return DeptSalesSelectResponse(return_value=1, error_message="Invalid Store", data=None)
        if request.week_ending_date is None or str(request.week_ending_date).strip() == '':
            return DeptSalesSelectResponse(return_value=1, error_message="Invalid Date", data=None)

        store = request.store
        week_end = request.week_ending_date

        with DBConnection() as conn:
            with conn.cursor() as cur:
                days_list = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                all_cats = ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                            'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other', 'Restaurant',
                            'FuelGrocery', 'Other3', 'Other4', 'Other5']
                sales = {cat: {day: Decimal('0.0') for day in days_list} for cat in all_cats}

                # Mon
                cur.execute(
                    """SELECT DDS_Grocery, DDS_Meat, DDS_Produce, DDS_Deli_Bakery, DDS_Florist, DDS_Seafood, DDS_Pharmacy, DDS_FF_Dairy, DDS_HBA, DDS_Sushi, DDS_Fuel, DDS_Starbucks, DDS_Kitchen_Ware, DDS_Dream_Dinners, DDS_Other FROM retail_history.daily_dept_sales WHERE DDS_Store = %s AND DDS_File_Date = %s""",
                    (store, week_end - timedelta(days=6)))
                row1 = cur.fetchone()
                if row1:
                    for i, cat in enumerate(
                            ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                             'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other']):
                        sales[cat]['Mon'] = row1[i] if row1[i] is not None else Decimal('0.0')

                cur.execute(
                    """SELECT DDSM_Restaurant, DDSM_FuelGrocery, DDSM_Other3, DDSM_Other4, DDSM_Other5 FROM retail_history.daily_dept_sales_manual WHERE DDSM_Store = %s AND DDSM_File_Date = %s""",
                    (store, week_end - timedelta(days=6)))
                row2 = cur.fetchone()
                if row2:
                    for i, cat in enumerate(['Restaurant', 'FuelGrocery', 'Other3', 'Other4', 'Other5']):
                        sales[cat]['Mon'] = row2[i] if row2[i] is not None else Decimal('0.0')

                # Tue
                cur.execute(
                    """SELECT DDS_Grocery, DDS_Meat, DDS_Produce, DDS_Deli_Bakery, DDS_Florist, DDS_Seafood, DDS_Pharmacy, DDS_FF_Dairy, DDS_HBA, DDS_Sushi, DDS_Fuel, DDS_Starbucks, DDS_Kitchen_Ware, DDS_Dream_Dinners, DDS_Other FROM retail_history.daily_dept_sales WHERE DDS_Store = %s AND DDS_File_Date = %s""",
                    (store, week_end - timedelta(days=5)))
                row1 = cur.fetchone()
                if row1:
                    for i, cat in enumerate(
                            ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                             'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other']):
                        sales[cat]['Tue'] = row1[i] if row1[i] is not None else Decimal('0.0')

                cur.execute(
                    """SELECT DDSM_Restaurant, DDSM_FuelGrocery, DDSM_Other3, DDSM_Other4, DDSM_Other5 FROM retail_history.daily_dept_sales_manual WHERE DDSM_Store = %s AND DDSM_File_Date = %s""",
                    (store, week_end - timedelta(days=5)))
                row2 = cur.fetchone()
                if row2:
                    for i, cat in enumerate(['Restaurant', 'FuelGrocery', 'Other3', 'Other4', 'Other5']):
                        sales[cat]['Tue'] = row2[i] if row2[i] is not None else Decimal('0.0')

                # Wed
                cur.execute(
                    """SELECT DDS_Grocery, DDS_Meat, DDS_Produce, DDS_Deli_Bakery, DDS_Florist, DDS_Seafood, DDS_Pharmacy, DDS_FF_Dairy, DDS_HBA, DDS_Sushi, DDS_Fuel, DDS_Starbucks, DDS_Kitchen_Ware, DDS_Dream_Dinners, DDS_Other FROM retail_history.daily_dept_sales WHERE DDS_Store = %s AND DDS_File_Date = %s""",
                    (store, week_end - timedelta(days=4)))
                row1 = cur.fetchone()
                if row1:
                    for i, cat in enumerate(
                            ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                             'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other']):
                        sales[cat]['Wed'] = row1[i] if row1[i] is not None else Decimal('0.0')

                cur.execute(
                    """SELECT DDSM_Restaurant, DDSM_FuelGrocery, DDSM_Other3, DDSM_Other4, DDSM_Other5 FROM retail_history.daily_dept_sales_manual WHERE DDSM_Store = %s AND DDSM_File_Date = %s""",
                    (store, week_end - timedelta(days=4)))
                row2 = cur.fetchone()
                if row2:
                    for i, cat in enumerate(['Restaurant', 'FuelGrocery', 'Other3', 'Other4', 'Other5']):
                        sales[cat]['Wed'] = row2[i] if row2[i] is not None else Decimal('0.0')

                # Thu
                cur.execute(
                    """SELECT DDS_Grocery, DDS_Meat, DDS_Produce, DDS_Deli_Bakery, DDS_Florist, DDS_Seafood, DDS_Pharmacy, DDS_FF_Dairy, DDS_HBA, DDS_Sushi, DDS_Fuel, DDS_Starbucks, DDS_Kitchen_Ware, DDS_Dream_Dinners, DDS_Other FROM retail_history.daily_dept_sales WHERE DDS_Store = %s AND DDS_File_Date = %s""",
                    (store, week_end - timedelta(days=3)))
                row1 = cur.fetchone()
                if row1:
                    for i, cat in enumerate(
                            ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                             'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other']):
                        sales[cat]['Thu'] = row1[i] if row1[i] is not None else Decimal('0.0')

                cur.execute(
                    """SELECT DDSM_Restaurant, DDSM_FuelGrocery, DDSM_Other3, DDSM_Other4, DDSM_Other5 FROM retail_history.daily_dept_sales_manual WHERE DDSM_Store = %s AND DDSM_File_Date = %s""",
                    (store, week_end - timedelta(days=3)))
                row2 = cur.fetchone()
                if row2:
                    for i, cat in enumerate(['Restaurant', 'FuelGrocery', 'Other3', 'Other4', 'Other5']):
                        sales[cat]['Thu'] = row2[i] if row2[i] is not None else Decimal('0.0')

                # Fri
                cur.execute(
                    """SELECT DDS_Grocery, DDS_Meat, DDS_Produce, DDS_Deli_Bakery, DDS_Florist, DDS_Seafood, DDS_Pharmacy, DDS_FF_Dairy, DDS_HBA, DDS_Sushi, DDS_Fuel, DDS_Starbucks, DDS_Kitchen_Ware, DDS_Dream_Dinners, DDS_Other FROM retail_history.daily_dept_sales WHERE DDS_Store = %s AND DDS_File_Date = %s""",
                    (store, week_end - timedelta(days=2)))
                row1 = cur.fetchone()
                if row1:
                    for i, cat in enumerate(
                            ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                             'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other']):
                        sales[cat]['Fri'] = row1[i] if row1[i] is not None else Decimal('0.0')

                cur.execute(
                    """SELECT DDSM_Restaurant, DDSM_FuelGrocery, DDSM_Other3, DDSM_Other4, DDSM_Other5 FROM retail_history.daily_dept_sales_manual WHERE DDSM_Store = %s AND DDSM_File_Date = %s""",
                    (store, week_end - timedelta(days=2)))
                row2 = cur.fetchone()
                if row2:
                    for i, cat in enumerate(['Restaurant', 'FuelGrocery', 'Other3', 'Other4', 'Other5']):
                        sales[cat]['Fri'] = row2[i] if row2[i] is not None else Decimal('0.0')

                # Sat
                cur.execute(
                    """SELECT DDS_Grocery, DDS_Meat, DDS_Produce, DDS_Deli_Bakery, DDS_Florist, DDS_Seafood, DDS_Pharmacy, DDS_FF_Dairy, DDS_HBA, DDS_Sushi, DDS_Fuel, DDS_Starbucks, DDS_Kitchen_Ware, DDS_Dream_Dinners, DDS_Other FROM retail_history.daily_dept_sales WHERE DDS_Store = %s AND DDS_File_Date = %s""",
                    (store, week_end - timedelta(days=1)))
                row1 = cur.fetchone()
                if row1:
                    for i, cat in enumerate(
                            ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                             'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other']):
                        sales[cat]['Sat'] = row1[i] if row1[i] is not None else Decimal('0.0')

                cur.execute(
                    """SELECT DDSM_Restaurant, DDSM_FuelGrocery, DDSM_Other3, DDSM_Other4, DDSM_Other5 FROM retail_history.daily_dept_sales_manual WHERE DDSM_Store = %s AND DDSM_File_Date = %s""",
                    (store, week_end - timedelta(days=1)))
                row2 = cur.fetchone()
                if row2:
                    for i, cat in enumerate(['Restaurant', 'FuelGrocery', 'Other3', 'Other4', 'Other5']):
                        sales[cat]['Sat'] = row2[i] if row2[i] is not None else Decimal('0.0')

                # Sun
                cur.execute(
                    """SELECT DDS_Grocery, DDS_Meat, DDS_Produce, DDS_Deli_Bakery, DDS_Florist, DDS_Seafood, DDS_Pharmacy, DDS_FF_Dairy, DDS_HBA, DDS_Sushi, DDS_Fuel, DDS_Starbucks, DDS_Kitchen_Ware, DDS_Dream_Dinners, DDS_Other FROM retail_history.daily_dept_sales WHERE DDS_Store = %s AND DDS_File_Date = %s""",
                    (store, week_end - timedelta(days=0)))
                row1 = cur.fetchone()
                if row1:
                    for i, cat in enumerate(
                            ['Grocery', 'Meat', 'Produce', 'Deli_Bakery', 'Florist', 'Seafood', 'Pharmacy', 'FF_Dairy',
                             'HBA', 'Sushi', 'Fuel', 'Starbucks', 'Kitchen_Ware', 'Dream_Dinners', 'Other']):
                        sales[cat]['Sun'] = row1[i] if row1[i] is not None else Decimal('0.0')

                cur.execute(
                    """SELECT DDSM_Restaurant, DDSM_FuelGrocery, DDSM_Other3, DDSM_Other4, DDSM_Other5 FROM retail_history.daily_dept_sales_manual WHERE DDSM_Store = %s AND DDSM_File_Date = %s""",
                    (store, week_end - timedelta(days=0)))
                row2 = cur.fetchone()
                if row2:
                    for i, cat in enumerate(['Restaurant', 'FuelGrocery', 'Other3', 'Other4', 'Other5']):
                        sales[cat]['Sun'] = row2[i] if row2[i] is not None else Decimal('0.0')

                # Totals
                tot_cat = {cat: sum(sales[cat][day] for day in days_list) for cat in all_cats}
                tot_day = {day: sum(sales[cat][day] for cat in all_cats) for day in days_list}
                total_sales = sum(tot_day.values())

                dist_day = {day: (tot_day[day] * 100 / total_sales) if total_sales != 0 else Decimal('0.0') for day in
                            days_list}
                dist_cat = {cat: (tot_cat[cat] * 100 / total_sales) if total_sales != 0 else Decimal('0.0') for cat in
                            all_cats}

                # Build report output (in-memory)
                data = []

                def add_row(desc, a1, t1, a2, t2, a3, t3, a4, t4, a5, t5, a6, t6, a7, t7, a8, t8, a9, t9):
                    data.append(DeptSalesSelectItem(
                        dsr_description=desc,
                        dsr_amount_1=str(a1) if a1 != '' else '', dsr_amount_1_type=t1,
                        dsr_amount_2=str(a2) if a2 != '' else '', dsr_amount_2_type=t2,
                        dsr_amount_3=str(a3) if a3 != '' else '', dsr_amount_3_type=t3,
                        dsr_amount_4=str(a4) if a4 != '' else '', dsr_amount_4_type=t4,
                        dsr_amount_5=str(a5) if a5 != '' else '', dsr_amount_5_type=t5,
                        dsr_amount_6=str(a6) if a6 != '' else '', dsr_amount_6_type=t6,
                        dsr_amount_7=str(a7) if a7 != '' else '', dsr_amount_7_type=t7,
                        dsr_amount_8=str(a8) if a8 != '' else '', dsr_amount_8_type=t8,
                        dsr_amount_9=str(a9) if a9 != '' else '', dsr_amount_9_type=t9
                    ))

                # Insert Report Heading 1
                add_row(f'Store: {store}', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '',
                        'B')
                # Insert Report Heading 2
                add_row(f'Wk Ending Date: {week_end.strftime("%m/%d/%y")}', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B',
                        '', 'B', '', 'B', '', 'B', '', 'B')
                # Insert Blank Line
                add_row('', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B')
                # Insert Column Headings (1)
                add_row('', 'Monday', 'H', 'Tuesday', 'H', 'Wednesday', 'H', 'Thursday', 'H', 'Friday', 'H', 'Saturday',
                        'H', 'Sunday', 'H', '', 'B', '', 'B')
                # Insert Column Headings (2)
                add_row('Department', (week_end - timedelta(days=6)).strftime('%m/%d'), 'H',
                        (week_end - timedelta(days=5)).strftime('%m/%d'), 'H',
                        (week_end - timedelta(days=4)).strftime('%m/%d'), 'H',
                        (week_end - timedelta(days=3)).strftime('%m/%d'), 'H',
                        (week_end - timedelta(days=2)).strftime('%m/%d'), 'H',
                        (week_end - timedelta(days=1)).strftime('%m/%d'), 'H', week_end.strftime('%m/%d'), 'H', 'Total',
                        'H', 'Dist', 'H')
                # Insert Blank Line
                add_row('------------------', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B',
                        '', 'B')

                if tot_cat['Grocery'] != 0:
                    add_row('Grocery', sales['Grocery']['Mon'], 'M', sales['Grocery']['Tue'], 'M',
                            sales['Grocery']['Wed'], 'M', sales['Grocery']['Thu'], 'M', sales['Grocery']['Fri'], 'M',
                            sales['Grocery']['Sat'], 'M', sales['Grocery']['Sun'], 'M', tot_cat['Grocery'], 'M',
                            dist_cat['Grocery'], 'P')
                if tot_cat['Meat'] != 0:
                    add_row('Meat', sales['Meat']['Mon'], 'M', sales['Meat']['Tue'], 'M', sales['Meat']['Wed'], 'M',
                            sales['Meat']['Thu'], 'M', sales['Meat']['Fri'], 'M', sales['Meat']['Sat'], 'M',
                            sales['Meat']['Sun'], 'M', tot_cat['Meat'], 'M', dist_cat['Meat'], 'P')
                if tot_cat['Produce'] != 0:
                    add_row('Produce', sales['Produce']['Mon'], 'M', sales['Produce']['Tue'], 'M',
                            sales['Produce']['Wed'], 'M', sales['Produce']['Thu'], 'M', sales['Produce']['Fri'], 'M',
                            sales['Produce']['Sat'], 'M', sales['Produce']['Sun'], 'M', tot_cat['Produce'], 'M',
                            dist_cat['Produce'], 'P')
                if tot_cat['Deli_Bakery'] != 0:
                    add_row('Deli/Bakery', sales['Deli_Bakery']['Mon'], 'M', sales['Deli_Bakery']['Tue'], 'M',
                            sales['Deli_Bakery']['Wed'], 'M', sales['Deli_Bakery']['Thu'], 'M',
                            sales['Deli_Bakery']['Fri'], 'M', sales['Deli_Bakery']['Sat'], 'M',
                            sales['Deli_Bakery']['Sun'], 'M', tot_cat['Deli_Bakery'], 'M', dist_cat['Deli_Bakery'], 'P')
                if tot_cat['Florist'] != 0:
                    add_row('Florist', sales['Florist']['Mon'], 'M', sales['Florist']['Tue'], 'M',
                            sales['Florist']['Wed'], 'M', sales['Florist']['Thu'], 'M', sales['Florist']['Fri'], 'M',
                            sales['Florist']['Sat'], 'M', sales['Florist']['Sun'], 'M', tot_cat['Florist'], 'M',
                            dist_cat['Florist'], 'P')
                if tot_cat['Seafood'] != 0:
                    add_row('Seafood', sales['Seafood']['Mon'], 'M', sales['Seafood']['Tue'], 'M',
                            sales['Seafood']['Wed'], 'M', sales['Seafood']['Thu'], 'M', sales['Seafood']['Fri'], 'M',
                            sales['Seafood']['Sat'], 'M', sales['Seafood']['Sun'], 'M', tot_cat['Seafood'], 'M',
                            dist_cat['Seafood'], 'P')
                if tot_cat['Pharmacy'] != 0:
                    add_row('Pharmacy', sales['Pharmacy']['Mon'], 'M', sales['Pharmacy']['Tue'], 'M',
                            sales['Pharmacy']['Wed'], 'M', sales['Pharmacy']['Thu'], 'M', sales['Pharmacy']['Fri'], 'M',
                            sales['Pharmacy']['Sat'], 'M', sales['Pharmacy']['Sun'], 'M', tot_cat['Pharmacy'], 'M',
                            dist_cat['Pharmacy'], 'P')
                if tot_cat['FF_Dairy'] != 0:
                    add_row('FF/Dairy', sales['FF_Dairy']['Mon'], 'M', sales['FF_Dairy']['Tue'], 'M',
                            sales['FF_Dairy']['Wed'], 'M', sales['FF_Dairy']['Thu'], 'M', sales['FF_Dairy']['Fri'], 'M',
                            sales['FF_Dairy']['Sat'], 'M', sales['FF_Dairy']['Sun'], 'M', tot_cat['FF_Dairy'], 'M',
                            dist_cat['FF_Dairy'], 'P')
                if tot_cat['HBA'] != 0:
                    add_row('HBA', sales['HBA']['Mon'], 'M', sales['HBA']['Tue'], 'M', sales['HBA']['Wed'], 'M',
                            sales['HBA']['Thu'], 'M', sales['HBA']['Fri'], 'M', sales['HBA']['Sat'], 'M',
                            sales['HBA']['Sun'], 'M', tot_cat['HBA'], 'M', dist_cat['HBA'], 'P')
                if tot_cat['Sushi'] != 0:
                    add_row('Sushi', sales['Sushi']['Mon'], 'M', sales['Sushi']['Tue'], 'M', sales['Sushi']['Wed'], 'M',
                            sales['Sushi']['Thu'], 'M', sales['Sushi']['Fri'], 'M', sales['Sushi']['Sat'], 'M',
                            sales['Sushi']['Sun'], 'M', tot_cat['Sushi'], 'M', dist_cat['Sushi'], 'P')
                if tot_cat['Fuel'] != 0:
                    add_row('Fuel', sales['Fuel']['Mon'], 'M', sales['Fuel']['Tue'], 'M', sales['Fuel']['Wed'], 'M',
                            sales['Fuel']['Thu'], 'M', sales['Fuel']['Fri'], 'M', sales['Fuel']['Sat'], 'M',
                            sales['Fuel']['Sun'], 'M', tot_cat['Fuel'], 'M', dist_cat['Fuel'], 'P')
                if tot_cat['Starbucks'] != 0:
                    add_row('Starbucks', sales['Starbucks']['Mon'], 'M', sales['Starbucks']['Tue'], 'M',
                            sales['Starbucks']['Wed'], 'M', sales['Starbucks']['Thu'], 'M', sales['Starbucks']['Fri'],
                            'M', sales['Starbucks']['Sat'], 'M', sales['Starbucks']['Sun'], 'M', tot_cat['Starbucks'],
                            'M', dist_cat['Starbucks'], 'P')
                if tot_cat['Kitchen_Ware'] != 0:
                    add_row('Kitchen Ware', sales['Kitchen_Ware']['Mon'], 'M', sales['Kitchen_Ware']['Tue'], 'M',
                            sales['Kitchen_Ware']['Wed'], 'M', sales['Kitchen_Ware']['Thu'], 'M',
                            sales['Kitchen_Ware']['Fri'], 'M', sales['Kitchen_Ware']['Sat'], 'M',
                            sales['Kitchen_Ware']['Sun'], 'M', tot_cat['Kitchen_Ware'], 'M', dist_cat['Kitchen_Ware'],
                            'P')
                if tot_cat['Dream_Dinners'] != 0:
                    add_row('Dream Dinners', sales['Dream_Dinners']['Mon'], 'M', sales['Dream_Dinners']['Tue'], 'M',
                            sales['Dream_Dinners']['Wed'], 'M', sales['Dream_Dinners']['Thu'], 'M',
                            sales['Dream_Dinners']['Fri'], 'M', sales['Dream_Dinners']['Sat'], 'M',
                            sales['Dream_Dinners']['Sun'], 'M', tot_cat['Dream_Dinners'], 'M',
                            dist_cat['Dream_Dinners'], 'P')
                if tot_cat['Other'] != 0:
                    add_row('Other', sales['Other']['Mon'], 'M', sales['Other']['Tue'], 'M', sales['Other']['Wed'], 'M',
                            sales['Other']['Thu'], 'M', sales['Other']['Fri'], 'M', sales['Other']['Sat'], 'M',
                            sales['Other']['Sun'], 'M', tot_cat['Other'], 'M', dist_cat['Other'], 'P')
                if tot_cat['Restaurant'] != 0:
                    add_row('Restaurant (Ind)', sales['Restaurant']['Mon'], 'M', sales['Restaurant']['Tue'], 'M',
                            sales['Restaurant']['Wed'], 'M', sales['Restaurant']['Thu'], 'M',
                            sales['Restaurant']['Fri'], 'M', sales['Restaurant']['Sat'], 'M',
                            sales['Restaurant']['Sun'], 'M', tot_cat['Restaurant'], 'M', dist_cat['Restaurant'], 'P')
                if tot_cat['FuelGrocery'] != 0:
                    add_row('Fuel Grocery (Ind)', sales['FuelGrocery']['Mon'], 'M', sales['FuelGrocery']['Tue'], 'M',
                            sales['FuelGrocery']['Wed'], 'M', sales['FuelGrocery']['Thu'], 'M',
                            sales['FuelGrocery']['Fri'], 'M', sales['FuelGrocery']['Sat'], 'M',
                            sales['FuelGrocery']['Sun'], 'M', tot_cat['FuelGrocery'], 'M', dist_cat['FuelGrocery'], 'P')
                if tot_cat['Other3'] != 0:
                    add_row('Floral  (Ind)', sales['Other3']['Mon'], 'M', sales['Other3']['Tue'], 'M',
                            sales['Other3']['Wed'], 'M', sales['Other3']['Thu'], 'M', sales['Other3']['Fri'], 'M',
                            sales['Other3']['Sat'], 'M', sales['Other3']['Sun'], 'M', tot_cat['Other3'], 'M',
                            dist_cat['Other3'], 'P')
                if tot_cat['Other4'] != 0:
                    add_row('Post Office (Ind)', sales['Other4']['Mon'], 'M', sales['Other4']['Tue'], 'M',
                            sales['Other4']['Wed'], 'M', sales['Other4']['Thu'], 'M', sales['Other4']['Fri'], 'M',
                            sales['Other4']['Sat'], 'M', sales['Other4']['Sun'], 'M', tot_cat['Other4'], 'M',
                            dist_cat['Other4'], 'P')
                if tot_cat['Other5'] != 0:
                    add_row('Fuel  (Ind)', sales['Other5']['Mon'], 'M', sales['Other5']['Tue'], 'M',
                            sales['Other5']['Wed'], 'M', sales['Other5']['Thu'], 'M', sales['Other5']['Fri'], 'M',
                            sales['Other5']['Sat'], 'M', sales['Other5']['Sun'], 'M', tot_cat['Other5'], 'M',
                            dist_cat['Other5'], 'P')

                # Insert Blank Line
                add_row('------------------', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B', '', 'B',
                        '', 'B')
                # Insert Daily/Weekly Totals
                add_row('Total Sales', tot_day['Mon'], 'M', tot_day['Tue'], 'M', tot_day['Wed'], 'M', tot_day['Thu'],
                        'M', tot_day['Fri'], 'M', tot_day['Sat'], 'M', tot_day['Sun'], 'M', total_sales, 'M', '', 'B')
                # Insert Daily Distribution
                add_row('Distribution', dist_day['Mon'], 'P', dist_day['Tue'], 'P', dist_day['Wed'], 'P',
                        dist_day['Thu'], 'P', dist_day['Fri'], 'P', dist_day['Sat'], 'P', dist_day['Sun'], 'P',
                        Decimal('100.0'), 'P', '', 'B')

                # Note: Deliberately skipping DB delete/insert into retail.dept_sales_report as requested for API modernizations, generating report in-memory.

                return DeptSalesSelectResponse(return_value=0, error_message="", data=data)

    except Exception as ex:
        logger.exception("Error in DeptSales_Select")
        return DeptSalesSelectResponse(return_value=1, error_message="Select Failed", data=None)



