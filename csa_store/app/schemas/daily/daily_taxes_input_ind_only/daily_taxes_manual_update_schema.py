from datetime import date
from uuid import UUID

from pydantic import BaseModel


class DailyTaxesManualUpdateRequest(BaseModel):
    """
    Request schema for:

    csa_DailyTaxes_Manual_Update
    """

    tenant_id: UUID

    dtm_store: int
    dtm_file_date: date

    dtm_net_sales1: float
    dtm_net_sales2: float
    dtm_net_sales3: float
    dtm_net_sales4: float

    dtm_sales_tax_collected1: float
    dtm_sales_tax_collected2: float
    dtm_sales_tax_collected3: float
    dtm_sales_tax_collected4: float

    user: str


class DailyTaxesManualUpdateResponse(BaseModel):
    """
    Response schema.
    """

    return_value: int
    error_message: str