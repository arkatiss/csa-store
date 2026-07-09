import logging
from fastapi import APIRouter
from app.core.db_utils import DBConnection
from app.schemas.reports.daily.form97_page12_select_schema import Form97Page12SelectRequest, Form97Page12SelectResponse, Form97Page12SelectItem

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports/daily",
    tags=["Reports Daily Form 97"]
)

@router.post("/form97_page12_select", response_model=Form97Page12SelectResponse)
def csa_form97_page12_select(request: Form97Page12SelectRequest):
    """
    Equivalent of:
    csa_Form97Page12_Select
    """
    try:
        if request.f97f_store is None or str(request.f97f_store).strip() == '':
            return Form97Page12SelectResponse(
                return_value=1,
                error_message="Invalid Store",
                data=None
            )
            
        if request.f97f_week_ending_date is None or str(request.f97f_week_ending_date).strip() == '':
            return Form97Page12SelectResponse(
                return_value=1,
                error_message="Invalid Date",
                data=None
            )

        with DBConnection() as conn:
            with conn.cursor() as cur:
                # Retrieve values
                cur.execute("""
                    SELECT 
                        f97f_line_number,
                        f97f_col1_description,
                        f97f_col1_amount,
                        f97f_col1_amount_type,
                        f97f_col2_description,
                        f97f_col2_amount,
                        f97f_col2_amount_type,
                        f97f_page_number
                    FROM retail.form97_formatted
                    WHERE f97f_store = %s 
                    AND f97f_week_ending_date = %s 
                    AND f97f_page_number < 3
                """, (request.f97f_store, request.f97f_week_ending_date))
                
                rows = cur.fetchall()
                data = []
                for row in rows:
                    item = Form97Page12SelectItem(
                        f97f_line_number=row[0],
                        f97f_col1_description=row[1],
                        f97f_col1_amount=row[2],
                        f97f_col1_amount_type=row[3],
                        f97f_col2_description=row[4],
                        f97f_col2_amount=row[5],
                        f97f_col2_amount_type=row[6],
                        f97f_page_number=row[7]
                    )
                    data.append(item)
                    
                return Form97Page12SelectResponse(
                    return_value=0,
                    error_message="",
                    data=data
                )

    except Exception as ex:
        logger.exception("Error in Form97Page12_Select")
        return Form97Page12SelectResponse(
            return_value=1,
            error_message="Select Failed",
            data=None
        )
