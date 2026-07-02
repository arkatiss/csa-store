from uuid import UUID
from pydantic import BaseModel

class Form102RetrieveByIDRequest(BaseModel):
    tenant_id: UUID
    def_id: int
