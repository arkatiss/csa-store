from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class WTDGrossProfitInventorySelectRequest(BaseModel):
    tenant_id: UUID
    wgi_store: Optional[int] = None
    wgi_week_ending_date: Optional[datetime] = None

class WTDGrossProfitInventoryItem(BaseModel):
    wgi_department: Optional[int] = None
    d_description: Optional[str] = None
    wgi_gross_profit: Optional[float] = None
    sda_gp_mf_account_nbr: Optional[str] = None
    wgi_ending_inventory: Optional[float] = None
    sda_ei_mf_account_nbr: Optional[str] = None

class WTDGrossProfitInventorySelectResponse(BaseModel):
    return_value: int
    error_message: str
    data: Optional[List[WTDGrossProfitInventoryItem]] = None
