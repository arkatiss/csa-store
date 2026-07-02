from pydantic import BaseModel
from datetime import date


class Form98RetrieveByKeyRequest(BaseModel):

    cb_store: int
    cb_date: date
    cb_employee_id: str
    cb_till: int