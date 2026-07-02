from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Form106DeleteRequest(BaseModel):

    tenant_id: UUID

    def_id: int

    def_store: int

    def_date: datetime

    def_form_type: int

    def_department: int

    def_user: str = Field(..., max_length=50)


