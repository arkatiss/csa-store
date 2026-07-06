from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional

class WTDNetReceiptsUpdateRequest(BaseModel):
    tenant_id: UUID
    wnr_store: Optional[int] = None
    wnr_week_ending_date: Optional[date] = None
    wnr_mo_receipts: Optional[float] = None
    wnr_nbr_of_mo: Optional[int] = None
    user: Optional[str] = None

class WTDNetReceiptsUpdateResponse(BaseModel):
    return_value: int
    error_message: str
