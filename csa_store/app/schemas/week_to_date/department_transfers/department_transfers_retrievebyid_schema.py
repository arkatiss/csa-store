from pydantic import BaseModel, Field
from typing import Optional,List
from datetime import datetime
from decimal import Decimal


class DepartmentTransferRequest(BaseModel):
    """
    Pydantic schema for the Department Transfer retrieval request.
    Matches the input parameter @DDT_ID.
    """
    ddt_id: Optional[int] = Field(None, description="The unique identifier for the Department Transfer record.")

class DepartmentTransferResponse(BaseModel):
    """
    Pydantic schema for the Department Transfer retrieval response.
    Matches all output parameters of the stored procedure.
    """
    ddt_id: Optional[int] = Field(None)
    ddt_store: Optional[int] = Field(None)
    ddt_to_store: Optional[int] = Field(None)
    ddt_date: Optional[datetime] = Field(None)
    ddt_from_department: Optional[int] = Field(None)
    d_from_description_desc: Optional[str] = Field(None)
    ddt_to_department: Optional[int] = Field(None)
    d_to_description_desc: Optional[str] = Field(None)
    ddt_item_quantity: Optional[int] = Field(None)
    ddt_item_description: Optional[str] = Field(None)
    ddt_user: Optional[str] = Field(None)
    ddt_retail_amount: Optional[Decimal] = Field(None)
    ddt_cost_amount: Optional[Decimal] = Field(None)
    return_value: int = Field(None)
    error_message: Optional[str] = Field(None)

    class Config:
        populate_by_name = True