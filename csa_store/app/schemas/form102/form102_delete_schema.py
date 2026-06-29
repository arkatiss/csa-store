from uuid import UUID
from pydantic import BaseModel
from datetime import date

class Form102DeleteRequest(BaseModel):
    tenant_id: UUID
    def_id: int
    def_store: int
    def_date: date
    def_form_type: int
    def_user: str
