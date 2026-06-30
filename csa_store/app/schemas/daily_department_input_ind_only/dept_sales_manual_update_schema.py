from pydantic import BaseModel
from uuid import UUID
from datetime import date

class DeptSalesManualUpdateRequest(BaseModel):
    tenant_id: UUID
    ddsm_store: int
    ddsm_file_date: date
    ddsm_restaurant: float
    ddsm_fuelgrocery: float
    ddsm_other3: float
    ddsm_other4: float
    ddsm_other5: float
    user: str
