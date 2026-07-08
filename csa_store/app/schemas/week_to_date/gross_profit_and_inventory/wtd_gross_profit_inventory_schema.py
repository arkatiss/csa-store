from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

# --- SCHEMAS (wtd_gross_profit_inventory_schema.py) ---

class WTDGrossProfitInventoryUpdateRequest(BaseModel):
    """
    Pydantic schema for WTD Gross Profit Inventory Update Request.
    Represents the input structure for the update API.
    """
    tenant_id: UUID
    wgi_store: int
    wgi_week_ending_date: datetime
    wgi_department: int
    wgi_gross_profit: Optional[float] = None
    wgi_ending_inventory: Optional[float] = None
    user: str

class WTDGrossProfitInventoryUpdateResponse(BaseModel):
    """
    Pydantic schema for WTD Gross Profit Inventory Update Response.
    """
    return_value: int
    error_message: str

