from datetime import date
from uuid import UUID

from pydantic import BaseModel


class Form111DeleteRequest(BaseModel):
    tenant_id: UUID

    def_id: int
    def_store: int
    def_date: date
    def_form_type: int
    def_user: str