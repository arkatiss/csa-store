from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date

class WTDTaxesRefundsSelectRequest(BaseModel):
    tenant_id: UUID
    wt_store: Optional[int] = None
    wt_week_ending_date: Optional[date] = None

class TaxRefundItem(BaseModel):
    wt_tax_rate: str
    wt_refunds: float

class WTDTaxesRefundsSelectResponse(BaseModel):
    return_value: int
    error_message: str
    tax_refunds: List[TaxRefundItem] = []
