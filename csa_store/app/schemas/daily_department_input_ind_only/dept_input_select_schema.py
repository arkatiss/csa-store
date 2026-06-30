from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import date

class DeptInputRow(BaseModel):
    row_description: str
    restaurant: float
    fuelgrocery: float
    other3: float
    other4: float
    other5: float

class DeptInputSelectRequest(BaseModel):
    tenant_id: UUID
    ddsm_store: int
    ddsm_file_date: date

class DeptInputSelectResponse(BaseModel):
    return_value: int
    error_message: str
    data: List[DeptInputRow] = []
