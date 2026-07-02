from uuid import UUID

from pydantic import BaseModel


class Form103SelectRequest(BaseModel):
    tenant_id: UUID

    def_store: int
    def_form_type: int
    def_department: int