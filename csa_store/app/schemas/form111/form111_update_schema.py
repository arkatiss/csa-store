from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class Form111UpdateRequest(BaseModel):
    tenant_id: UUID

    def_id: int
    def_store: int
    def_date: date
    def_form_type: int

    def_user: str

    def_descriptor_1: str
    def_descriptor_2: str | None = None

    def_amount_1: Decimal
    def_amount_2: Decimal