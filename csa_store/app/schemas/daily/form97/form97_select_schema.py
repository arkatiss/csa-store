from datetime import date
from uuid import UUID

from pydantic import BaseModel


class Form97SelectRequest(BaseModel):
    tenant_id: UUID
    ob_store: int
    ob_date: date