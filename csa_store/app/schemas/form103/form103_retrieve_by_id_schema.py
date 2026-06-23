from pydantic import BaseModel


class Form103RetrieveByIdRequest(BaseModel):
    tenant_id: str
    def_id: int