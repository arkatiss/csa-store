from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date

class WTDNetReceiptsSelectRequest(BaseModel):
    tenant_id: UUID
    wnr_store: Optional[int] = None
    wnr_week_ending_date: Optional[date] = None

class WTDNetReceiptsSelectResponse(BaseModel):
    return_value: int
    error_message: str
    wnr_form111_total: Optional[float] = None
    wnr_ar_collected: Optional[float] = None
    wnr_mo_receipts: Optional[float] = None
    wnr_nbr_of_mo: Optional[int] = None
