from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional


class WTDNetSalesUpdateRequest(BaseModel):
    """
    Request Schema
    Equivalent to:
    csa_WTDNetSales_Update
    """

    tenant_id: UUID

    wns_store: int

    wns_week_ending_date: datetime

    wns_deposit_cancels: Optional[Decimal] = Field(
        default=None,
        max_digits=19,
        decimal_places=4
    )

    wns_other_sales: Optional[Decimal] = Field(
        default=None,
        max_digits=19,
        decimal_places=4
    )

    wns_other_sales_description: Optional[str] = Field(
        default=None,
        max_length=50
    )

    user: str = Field(
        ...,
        max_length=50
    )


class WTDNetSalesUpdateResponse(BaseModel):
    """
    Response Schema
    """

    return_value: int

    error_message: str