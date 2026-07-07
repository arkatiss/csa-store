from pydantic import BaseModel, Field
from typing import Optional,List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class DepartmentTransferUpdateRequest(BaseModel):
    tenant_id: UUID
    ddt_id: int = Field(..., alias="DDT_ID")
    ddt_store: int = Field(..., alias="DDT_Store")
    ddt_to_store: Optional[int] = Field(None, alias="DDT_To_Store")
    ddt_date: datetime = Field(..., alias="DDT_Date")
    ddt_from_department: int = Field(..., alias="DDT_From_Department")
    ddt_to_department: int = Field(..., alias="DDT_To_Department")
    ddt_item_quantity: int = Field(..., alias="DDT_Item_Quantity")
    ddt_item_description: str = Field(..., max_length=50, alias="DDT_Item_Description")
    ddt_user: str = Field(..., max_length=50, alias="DDT_User")
    ddt_retail_amount: Decimal = Field(..., alias="DDT_Retail_Amount")
    ddt_cost_amount: Decimal = Field(..., alias="DDT_Cost_Amount")

    class Config:
        populate_by_name = True

class UpdateResponse(BaseModel):
    return_value: int
    error_message: Optional[str] = ""
