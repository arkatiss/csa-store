from pydantic import BaseModel
from decimal import Decimal
from datetime import date


class Form98InsertRequest(BaseModel):
    cb_store: int
    cb_date: date
    cb_employee_id: str
    cb_till: int
    cb_name: str

    cb_sales: Decimal
    cb_voids: Decimal
    cb_returns: Decimal
    cb_checks: Decimal

    cb_gift_cards_tendered: Decimal
    cb_ebt: Decimal
    cb_credit_cards: Decimal
    cb_wic: Decimal

    cb_charges: Decimal
    cb_debit_cards: Decimal

    cb_vendor_coupons: Decimal
    cb_pfc_coupons: Decimal

    cb_cashier_over_short: Decimal

    cb_user: str

    cb_promo_coupons: Decimal
    cb_miscellaneous: Decimal