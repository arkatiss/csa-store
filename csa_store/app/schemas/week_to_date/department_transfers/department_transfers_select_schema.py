from pydantic import BaseModel
from typing import Optional,List
from datetime import datetime
from decimal import Decimal


class DepartmentTransferRequest(BaseModel):
    """
    Schema for the input parameters of the department transfers selection.
    Equivalent to @DDT_Store input parameter.
    """
    ddt_store: Optional[int] = None


class DepartmentTransferItem(BaseModel):
    """
    Schema representing a single department transfer record.
    Maps to the columns returned by the SELECT statement.
    """
    ddt_id: int
    ddt_date: Optional[datetime] = None
    ddt_from_department: Optional[int] = None
    d_from_department_desc: Optional[str] = None
    ddt_to_department: Optional[int] = None
    d_to_department_desc: Optional[str] = None
    ddt_item_quantity: Optional[int] = None
    ddt_item_description: Optional[str] = None
    ddt_user: Optional[str] = None
    ddt_retail_amount: Optional[Decimal] = None
    ddt_cost_amount: Optional[Decimal] = None
    ddt_to_store: Optional[int] = None

class DepartmentTransferResponse(BaseModel):
    """
    Schema for the API response, including output parameters and data.
    Equivalent to @Return_Value and @Error_Message output parameters.
    """
    return_value: int
    error_message: Optional[str] = None
    data: List[DepartmentTransferItem]