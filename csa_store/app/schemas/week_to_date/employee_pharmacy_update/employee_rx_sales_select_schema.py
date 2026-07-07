from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date

class EmployeeRXSalesSelectRequest(BaseModel):
    tenant_id: UUID
    store: Optional[int] = None
    week_ending_date: Optional[date] = None

class EmployeeRXSalesSelectResponse(BaseModel):
    return_value: int
    error_message: str
    wds_pharmacy: Optional[float] = None
    wcc_pharmacy: Optional[int] = None
    wds_employee_rx: Optional[float] = None
    wcc_employee_rx: Optional[int] = None
