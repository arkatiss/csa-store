from uuid import UUID

from pydantic import BaseModel


class Form111RetrieveByIdRequest(BaseModel):
    tenant_id: UUID
    def_id: int