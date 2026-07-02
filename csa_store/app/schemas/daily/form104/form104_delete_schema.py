# app/schemas/form104/form104_delete_schema.py

from datetime import date
from pydantic import BaseModel
from uuid import UUID


class Form104DeleteRequest(BaseModel):
    tenant_id: UUID
    def_id: int
    def_store: int
    def_date: date
    def_form_type: int
    def_department: int
    def_user: str