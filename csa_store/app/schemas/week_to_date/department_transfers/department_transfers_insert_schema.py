from pydantic import BaseModel, Field
from typing import Optional,List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class DepartmentTransferRequest(BaseModel):
    """
    Pydantic schema for the Department Transfer insertion request.
    Matches the input parameters of csa_DepartmentTransfers_Insert.
    """
    tenant_id: UUID
    ddt_store: int = Field(..., description="The source store ID (DDT_Store)")
    ddt_to_store: int = Field(..., description="The destination store ID (DDT_To_Store)")
    ddt_date: datetime = Field(..., description="The date of the transfer (DDT_Date)")
    ddt_from_department: int = Field(..., description="The source department ID (DDT_From_Department)")
    ddt_to_department: int = Field(..., description="The destination department ID (DDT_To_Department)")
    ddt_item_quantity: int = Field(..., description="Quantity of items (DDT_Item_Quantity)")
    ddt_item_description: str = Field(..., max_length=50, description="Description of the item (DDT_Item_Description)")
    ddt_user: str = Field(..., max_length=50, description="User performing the transfer (DDT_User)")
    ddt_retail_amount: float = Field(..., description="Retail amount (DDT_Retail_Amount)")
    ddt_cost_amount: float = Field(..., description="Cost amount (DDT_Cost_Amount)")

class DepartmentTransferResponse(BaseModel):
    """
    Pydantic schema for the Department Transfer response.
    Matches the output parameters of csa_DepartmentTransfers_Insert.
    """
    return_value: int = Field(..., description="0 for success, 1 for failure")
    error_message: Optional[str] = Field(None, description="Error message if return_value is 1")
    id: Optional[int] = Field(None, description="The identity of the inserted row")