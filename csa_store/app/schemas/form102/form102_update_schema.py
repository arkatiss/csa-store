from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import date

class Form102UpdateRequest(BaseModel):
    tenant_id: UUID
    def_id: int
    def_store: int
    def_date: date
    def_form_type: int
    def_user: str
    def_descriptor_1: str
    def_descriptor_2: Optional[str] = None
    def_amount_2: float
