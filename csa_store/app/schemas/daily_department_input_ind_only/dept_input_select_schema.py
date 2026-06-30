from pydantic import BaseModel
from typing import List

class DeptInputRow(BaseModel):
    row_description: str
    restaurant: float
    fuelgrocery: float
    other3: float
    other4: float
    other5: float

class DeptInputSelectResponse(BaseModel):
    return_value: int
    error_message: str
    data: List[DeptInputRow] = []
