from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date

class FormPOSInitRequest(BaseModel):
    tenant_id: UUID
    pos_store: Optional[int] = None
    pos_file_date: Optional[date] = None
    user: Optional[str] = None

class FormPOSInitResponse(BaseModel):
    return_value: int
    error_message: str
