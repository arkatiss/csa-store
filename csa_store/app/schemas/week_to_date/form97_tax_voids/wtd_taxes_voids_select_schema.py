from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date

class WTDTaxesVoidsSelectRequest(BaseModel):
    tenant_id: UUID
    wt_store: Optional[int] = None
    wt_week_ending_date: Optional[date] = None

class TaxVoidItem(BaseModel):
    wt_tax_rate: str
    wt_voids: float

class WTDTaxesVoidsSelectResponse(BaseModel):
    return_value: int
    error_message: str
    tax_voids: List[TaxVoidItem] = []
