from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class Form122UpdateRequest(BaseModel):
    tenant_id: str
    psi_store: int
    psi_date: date

    psi_books_received: int
    psi_money_collected: Decimal
    psi_books_sold: int
    psi_books_in_till: int
    psi_books_in_safe: int
    psi_books_in_office: int

    user: str