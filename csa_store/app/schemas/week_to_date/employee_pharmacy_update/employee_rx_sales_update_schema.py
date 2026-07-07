from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date

class EmployeeRXSalesUpdateRequest(BaseModel):
    tenant_id: UUID
    store: Optional[int] = None
    week_ending_date: Optional[date] = None
    weekly_sales: Optional[float] = None
    weekly_customer_count: Optional[int] = None
    user: Optional[str] = None

class EmployeeRXSalesUpdateResponse(BaseModel):
    return_value: int
    error_message: str
