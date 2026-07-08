### File 1: schema.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

class WTDNonDepositableItemsUpdateRequest(BaseModel):
    """
    Pydantic schema for WTD Non Depositable Items update request.
    Matches the structure of retail_accounting.wtd_non_depositable_items table.
    """
    tenant_id: UUID
    wndi_store: int
    wndi_week_ending_date: datetime
    wndi_cash_savers: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=4)
    wndi_gift_certificates: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=4)
    wndi_vendor_coupons: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=4)
    wndi_third_party_rx: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=4)
    wndi_miscellaneous: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=4)
    wndi_pfc_coupons: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=4)
    wndi_elec_gbax_coupons: Optional[Decimal] = Field(default=None, max_digits=19, decimal_places=4)
    user: str

class WTDNonDepositableItemsUpdateResponse(BaseModel):
    """
    Pydantic schema for WTD Non Depositable Items update response.
    """
    return_value: int
    error_message: str
