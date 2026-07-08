from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class WTDNonDepositableItemsSelectRequest(BaseModel):
    tenant_id: UUID
    wndi_store: Optional[int] = None
    wndi_week_ending_date: Optional[datetime] = None

class WTDNonDepositableItemsSelectResponse(BaseModel):
    return_value: int
    error_message: str

    wndi_cash_savers: Optional[float] = None
    wndi_gift_certificates: Optional[float] = None
    wndi_vendor_coupons: Optional[float] = None
    wndi_third_party_rx: Optional[float] = None
    wndi_miscellaneous: Optional[float] = None
    wndi_pfc_coupons: Optional[float] = None
    wndi_elec_gbax_coupons: Optional[float] = None
