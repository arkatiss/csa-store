from uuid import UUID

from pydantic import BaseModel


class Form111SelectRequest(BaseModel):
    tenant_id: UUID
    def_store: int
    def_form_type: int