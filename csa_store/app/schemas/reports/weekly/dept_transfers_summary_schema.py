from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DeptTransfersSummaryRequest(BaseModel):
    store: Optional[int] = None
    week_ending_date: Optional[datetime] = None

class DeptTransfersSummaryItem(BaseModel):
    store: int
    department: int
    description: str
    retail: str
    retail_type: str
    cost: str
    cost_type: str

class DeptTransfersSummaryResponse(BaseModel):
    return_value: int
    error_message: str
    data: Optional[List[DeptTransfersSummaryItem]] = None
