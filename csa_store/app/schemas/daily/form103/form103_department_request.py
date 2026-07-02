from pydantic import BaseModel


class Form103DepartmentRequest(BaseModel):
    store: int