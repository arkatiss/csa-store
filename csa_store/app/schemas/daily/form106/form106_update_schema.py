from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class Form106UpdateRequest(BaseModel):

    tenant_id: UUID

    def_id: int

    def_store: int

    def_date: datetime

    def_form_type: int

    def_department: int

    def_user: str = Field(..., max_length=50)

    def_descriptor_1: str = Field(..., max_length=50)

    def_descriptor_2: str = Field(..., max_length=50)

    def_amount_2: Decimal