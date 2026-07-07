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
    ddt_store: Optional[int] = Field(None, alias="DDT_Store")
    ddt_to_store: Optional[int] = Field(None, alias="DDT_To_Store")
    ddt_date: Optional[datetime] = Field(None, alias="DDT_Date")
    ddt_from_department: Optional[int] = Field(None, alias="DDT_From_Department")
    d_from_description: Optional[str] = Field(None, alias="D_From_Description")
    ddt_to_department: Optional[int] = Field(None, alias="DDT_To_Department")
    d_to_description: Optional[str] = Field(None, alias="D_To_Description")
    ddt_item_quantity: Optional[int] = Field(None, alias="DDT_Item_Quantity")
    ddt_item_description: Optional[str] = Field(None, alias="DDT_Item_Description")
    ddt_user: Optional[str] = Field(None, alias="DDT_User")
    ddt_retail_amount: Optional[Decimal] = Field(None, alias="DDT_Retail_Amount")
    ddt_cost_amount: Optional[Decimal] = Field(None, alias="DDT_Cost_Amount")
    return_value: int = Field(..., alias="Return_Value")
    error_message: Optional[str] = Field(None, alias="Error_Message")

    class Config:
        populate_by_name = True