from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

class Form98SelectRequest(BaseModel):
    cb_store: Optional[int] = None

class Form98SelectItem(BaseModel):
    cb_date: date
    cb_employee_id: str
    cb_till: int
    cb_name: Optional[str] = None
    cb_sales: Optional[Decimal] = None
    cb_voids: Optional[Decimal] = None
    cb_returns: Optional[Decimal] = None
    cb_checks: Optional[Decimal] = None
    cb_gift_cards_tendered: Optional[Decimal] = None
    cb_ebt: Optional[Decimal] = None
    cb_credit_cards: Optional[Decimal] = None
    cb_wic: Optional[Decimal] = None
    cb_charges: Optional[Decimal] = None
    cb_debit_cards: Optional[Decimal] = None
    cb_vendor_coupons: Optional[Decimal] = None
    cb_pfc_coupons: Optional[Decimal] = None
    cb_cashier_over_short: Optional[Decimal] = None
    cb_user: str
    cb_promo_coupons: Optional[Decimal] = None
    cb_miscellaneous: Optional[Decimal] = None

class Form98SelectResponse(BaseModel):
    return_value: int
    error_message: str
    data: Optional[List[Form98SelectItem]] = None
