from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class Form97UpdateRequest(BaseModel):
    tenant_id: UUID

    ob_store: int
    ob_date: date

    ob_petty_cash_advances: Decimal

    ob_currency_in_safe: Decimal
    ob_coin_in_safe: Decimal

    ob_currency_in_office: Decimal
    ob_coin_in_office: Decimal

    ob_checks: Decimal
    ob_returned_checks: Decimal

    ob_food_stamps: Decimal
    ob_bank_cards: Decimal

    ob_paid_outs_cd: Decimal
    ob_employee_loans: Decimal

    ob_register_tills: Decimal
    ob_atm_machine: Decimal

    ob_miscellaneous_1: Decimal
    ob_miscellaneous_1_description: str | None = None

    ob_miscellaneous_2: Decimal
    ob_miscellaneous_2_description: str | None = None

    user: str