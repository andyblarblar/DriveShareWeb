import datetime
from functools import reduce
from typing import Optional, Sequence

from sqlmodel import SQLModel, Field
from sqlalchemy import PrimaryKeyConstraint
from pydantic import BaseModel


class AccountDTO(SQLModel):
    email: str = Field(primary_key=True)
    balance: float


class Account(AccountDTO, table=True):
    password: str
    secq1: str
    secq2: str
    secq3: str


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner: str = Field(foreign_key="account.email")
    model: str
    year: int
    mileage: int
    """Miles on car"""
    location: str
    """Unformatted location"""
    price: float
    """Price per day"""


class ReservationDTO(SQLModel):
    listing_id: int = Field(foreign_key="listing.id")
    """ID of listing this reservation is for"""
    start_date: datetime.date
    end_date: datetime.date


class Reservation(ReservationDTO, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner: str = Field(foreign_key="account.email")
    """The account reserving"""


class ReviewDTO(SQLModel):
    reservation_id: int = Field(foreign_key="reservation.id")
    """Reservation this review is for"""
    text: str
    """Review text"""
    rating: int
    """1-5 star rating"""


class Review(ReviewDTO, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner: str = Field(foreign_key="account.email")
    """Reviewer email"""


class AvailableDateRange(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.id")
    """Listing this date range is valid for"""
    start_date: datetime.date
    end_date: datetime.date

    def to_ranges(self) -> list[tuple[datetime.date, datetime.date]]:
        return [(self.start_date, self.end_date)]


# DTOs not in DB
class NewListingDTO(BaseModel):
    model: str
    year: int
    mileage: int
    """Miles on car"""
    location: str
    """Unformatted location"""
    price: float
    """Price per day"""
    date_ranges: list[tuple[datetime.date, datetime.date]]
    """List of (start, end) dates this listing is valid for"""


class ExistingListingDTO(NewListingDTO):
    id: int
    owner: str

    @staticmethod
    def from_orm_parts(listing: Listing, ranges: Sequence[AvailableDateRange]):
        return ExistingListingDTO(**listing.model_dump(),
                                  date_ranges=reduce(lambda x, y: x + y, (r.to_ranges() for r in ranges)))


class PasswordResetDTO(BaseModel):
    email: str
    new_password: str
    q1: str
    q2: str
    q3: str
