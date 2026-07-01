import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.daily_taxes_input_ind_only.daily_taxes_manual_select_schema import DailyTaxesManualSelectRequest, DailyTaxesManualSelectResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/daily_taxes_input_ind_only",
    tags=["Daily Taxes Input Ind Only"]
)

@router.post("/manual_select", response_model=DailyTaxesManualSelectResponse)
def csa_daily_taxes_manual_select(request: DailyTaxesManualSelectRequest):
    """
    Equivalent of:
    csa_DailyTaxes_Manual_Select
    """
    try:
        if request.dtm_store is None:
            return DailyTaxesManualSelectResponse(
                return_value=1,
                error_message="Invalid Store"
            )
        if request.dtm_file_date is None:
            return DailyTaxesManualSelectResponse(
                return_value=2,
                error_message="Invalid Date"
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Check if rows exist
                cur.execute("""
                    SELECT count(*)
                    FROM retail_history.daily_taxes_manual
                    WHERE dtm_store = %s AND dtm_file_date = %s
                """, (request.dtm_store, request.dtm_file_date))
                
                count_record = cur.fetchone()
                if not count_record or count_record[0] == 0:
                    return DailyTaxesManualSelectResponse(
                        return_value=3,
                        error_message="Row not found"
                    )

                # Fetch all relevant rows
                cur.execute("""
                    SELECT dtm_tax_rate, dtm_net_sales, dtm_sales_tax_collected
                    FROM retail_history.daily_taxes_manual
                    WHERE dtm_store = %s AND dtm_file_date = %s
                """, (request.dtm_store, request.dtm_file_date))
                
                rows = cur.fetchall()
                
                # Initialize variables
                net_sales = { '1': None, '2': None, '3': None, '4': None }
                tax_collected = { '1': None, '2': None, '3': None, '4': None }

                # Map data based on tax rate
                for row in rows:
                    tax_rate = str(row[0]).strip()
                    if tax_rate in net_sales:
                        net_sales[tax_rate] = float(row[1]) if row[1] is not None else 0.0
                        tax_collected[tax_rate] = float(row[2]) if row[2] is not None else 0.0

                return DailyTaxesManualSelectResponse(
                    return_value=0,
                    error_message="",
                    dtm_daily_net_sales_rate_1=net_sales['1'],
                    dtm_daily_net_sales_rate_2=net_sales['2'],
                    dtm_daily_net_sales_rate_3=net_sales['3'],
                    dtm_daily_net_sales_rate_4=net_sales['4'],
                    dtm_daily_sales_tax_collected_rate_1=tax_collected['1'],
                    dtm_daily_sales_tax_collected_rate_2=tax_collected['2'],
                    dtm_daily_sales_tax_collected_rate_3=tax_collected['3'],
                    dtm_daily_sales_tax_collected_rate_4=tax_collected['4']
                )

    except Exception as ex:
        logger.exception("Error in DailyTaxes_Manual_Select")
        return DailyTaxesManualSelectResponse(
            return_value=1,
            error_message="Select Daily Taxes (Manual) Failed"
        )
