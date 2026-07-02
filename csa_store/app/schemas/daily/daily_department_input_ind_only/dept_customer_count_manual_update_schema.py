from pydantic import BaseModel
from uuid import UUID
from datetime import date

class DeptCustomerCountManualUpdateRequest(BaseModel):
    tenant_id: UUID
    dccm_store: int
    dccm_file_date: date
    dccm_restaurant: int
    dccm_fuelgrocery: int
    dccm_other3: int
    dccm_other4: int
    dccm_other5: int
    user: str
