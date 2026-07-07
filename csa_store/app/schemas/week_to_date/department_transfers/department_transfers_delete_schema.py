from pydantic import BaseModel, Field
from typing import Optional,List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class DepartmentTransferDeleteRequest(BaseModel):
    """
    Input schema for deleting a department transfer.
    Matches the parameters of csa_DepartmentTransfers_Delete.
    """
    tenant_id: UUID = Field(..., description="The unique identifier for the tenant")
    ddt_id: int = Field(..., description="The Identity ID of the transfer to delete")
    ddt_user: str = Field(..., max_length=50, description="The user performing the delete")

class DepartmentTransferDeleteResponse(BaseModel):
    """
    Output schema for the delete operation.
    Matches the Output parameters of csa_DepartmentTransfers_Delete.
    """
    return_value: int
    error_message: Optional[str] = ""