import datetime

from sqlmodel import create_engine, SQLModel, Session, select
from ..security.password import hash_password
# Required to create tables below
from ..orm.model import *

sqlite_file_name = "db.sqlite"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})


def prepare_db():
    # Create tables if not exists
    SQLModel.metadata.create_all(engine)

    with Session(engine) as sess:
        # Populate DB with demo accounts if not done so far
        if not sess.get(Account, "avealov@umich.edu"):
            a1 = Account(email="avealov@umich.edu", password=hash_password("123"), secq1="asd", secq2="asd",
                         secq3="asd")
            sess.add(a1)

            l1 = Listing(owner=a1.email, model="Mazda Miata", year=2004, mileage=50000, location="Dearborn, MI",
                         price=40.5)
            sess.add(l1)
            sess.commit()

            d1 = AvailableDateRange(listing_id=l1.id, start_date=datetime.datetime(2024, 5, 22),
                                    end_date=datetime.datetime(2024, 8, 12))
            sess.add(d1)
            sess.commit()
