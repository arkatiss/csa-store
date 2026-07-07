from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class DTDepartmentsSelectRequest(BaseModel):
    tenant_id: UUID
    store: Optional[int] = None

class DepartmentItem(BaseModel):
    d_id: int
    d_description: str

class DTDepartmentsSelectResponse(BaseModel):
    return_value: int
    error_message: str
    departments: List[DepartmentItem] = []
