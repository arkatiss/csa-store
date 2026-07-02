from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class Form112UpdateRequest(BaseModel):
    tenant_id: UUID
    dms_store: int
    dms_date: date
    dms_machine_nbr: int
    dms_ending_reading: int | None = None
    dms_nbr_of_sales: int | None = None
    dms_actual_sales: Decimal
    created_by: str