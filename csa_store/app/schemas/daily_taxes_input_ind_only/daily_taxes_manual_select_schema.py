from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date

class DailyTaxesManualSelectRequest(BaseModel):
    tenant_id: UUID
    dtm_store: int
    dtm_file_date: date

class DailyTaxesManualSelectResponse(BaseModel):
    return_value: int
    error_message: str
    dtm_daily_net_sales_rate_1: Optional[float] = None
    dtm_daily_net_sales_rate_2: Optional[float] = None
    dtm_daily_net_sales_rate_3: Optional[float] = None
    dtm_daily_net_sales_rate_4: Optional[float] = None
    dtm_daily_sales_tax_collected_rate_1: Optional[float] = None
    dtm_daily_sales_tax_collected_rate_2: Optional[float] = None
    dtm_daily_sales_tax_collected_rate_3: Optional[float] = None
    dtm_daily_sales_tax_collected_rate_4: Optional[float] = None
