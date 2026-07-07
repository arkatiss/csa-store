from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date

class WTDNetSalesSelectRequest(BaseModel):
    tenant_id: UUID
    wns_store: Optional[int] = None
    wns_week_ending_date: Optional[date] = None

class WTDNetSalesSelectResponse(BaseModel):
    return_value: int
    error_message: str
    wns_current_group_reading: Optional[float] = None
    wns_previous_group_reading: Optional[float] = None
    wns_gross_receipts: Optional[float] = None
    wns_voids: Optional[float] = None
    wns_refunds: Optional[float] = None
    wns_tax_credits: Optional[float] = None
    wns_store_coupons: Optional[float] = None
    wns_other_sales: Optional[float] = None
    wns_other_sales_description: Optional[str] = None
