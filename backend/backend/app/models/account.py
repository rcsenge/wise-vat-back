from decimal import Decimal

from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    currency: str = Field(max_length=3)
    balance: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
