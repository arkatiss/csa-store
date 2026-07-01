from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional

class DailyTaxesManualUpdateRequest(BaseModel):
    tenant_id: UUID
    dtm_store: Optional[int] = None
    dtm_file_date: Optional[date] = None
    dtm_net_sales1: Optional[float] = None
    dtm_net_sales2: Optional[float] = None
    dtm_net_sales3: Optional[float] = None
    dtm_net_sales4: Optional[float] = None
    dtm_sales_tax_collected1: Optional[float] = None
    dtm_sales_tax_collected2: Optional[float] = None
    dtm_sales_tax_collected3: Optional[float] = None
    dtm_sales_tax_collected4: Optional[float] = None
    user: Optional[str] = None

class DailyTaxesManualUpdateResponse(BaseModel):
    return_value: int
    error_message: str
