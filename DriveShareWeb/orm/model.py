from sqlmodel import SQLModel, Field
from sqlalchemy import PrimaryKeyConstraint


class AccountDTO(SQLModel):
    email: str = Field(primary_key=True)


class Account(AccountDTO, table=True):
    password: str
    secq1: str
    secq2: str
    secq3: str
