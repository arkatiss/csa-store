from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

class Form97Page12SelectRequest(BaseModel):
    f97f_store: Optional[int] = None
    f97f_week_ending_date: Optional[date] = None

class Form97Page12SelectItem(BaseModel):
    f97f_line_number: int
    f97f_col1_description: str
    f97f_col1_amount: Decimal
    f97f_col1_amount_type: str
    f97f_col2_description: str
    f97f_col2_amount: Decimal
    f97f_col2_amount_type: str
    f97f_page_number: int

class Form97Page12SelectResponse(BaseModel):
    return_value: int
    error_message: str
    data: Optional[List[Form97Page12SelectItem]] = None
