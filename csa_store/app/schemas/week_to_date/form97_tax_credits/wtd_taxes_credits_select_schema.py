from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date

class WTDTaxesCreditsSelectRequest(BaseModel):
    tenant_id: UUID
    wt_store: Optional[int] = None
    wt_week_ending_date: Optional[date] = None

class TaxCreditItem(BaseModel):
    wt_tax_rate: str
    wt_credits: float

class WTDTaxesCreditsSelectResponse(BaseModel):
    return_value: int
    error_message: str
    tax_credits: List[TaxCreditItem] = []
