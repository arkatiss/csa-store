from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

class DeptSalesSelectRequest(BaseModel):
    store: Optional[int] = None
    week_ending_date: Optional[date] = None

class DeptSalesSelectItem(BaseModel):
    dsr_description: str
    dsr_amount_1: Optional[str] = None
    dsr_amount_1_type: Optional[str] = None
    dsr_amount_2: Optional[str] = None
    dsr_amount_2_type: Optional[str] = None
    dsr_amount_3: Optional[str] = None
    dsr_amount_3_type: Optional[str] = None
    dsr_amount_4: Optional[str] = None
    dsr_amount_4_type: Optional[str] = None
    dsr_amount_5: Optional[str] = None
    dsr_amount_5_type: Optional[str] = None
    dsr_amount_6: Optional[str] = None
    dsr_amount_6_type: Optional[str] = None
    dsr_amount_7: Optional[str] = None
    dsr_amount_7_type: Optional[str] = None
    dsr_amount_8: Optional[str] = None
    dsr_amount_8_type: Optional[str] = None
    dsr_amount_9: Optional[str] = None
    dsr_amount_9_type: Optional[str] = None

class DeptSalesSelectResponse(BaseModel):
    return_value: int
    error_message: str
    data: Optional[List[DeptSalesSelectItem]] = None
