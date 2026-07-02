from pydantic import BaseModel
from uuid import UUID
from datetime import date

class DeptVoidsRefundsManualUpdateRequest(BaseModel):
    tenant_id: UUID
    ddvrm_store: int
    ddvrm_file_date: date
    ddvrm_restaurant: float
    ddvrm_fuelgrocery: float
    ddvrm_other3: float
    ddvrm_other4: float
    ddvrm_other5: float
    user: str
