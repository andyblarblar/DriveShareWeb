from functools import reduce
from typing import Annotated
import datetime

from fastapi import FastAPI, Depends, HTTPException, Response, Request, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from starlette import status
from starlette.responses import RedirectResponse

from DriveShareWeb.deps import ensure_user_not_logged_in, get_current_user, db_session, get_payment_service
from DriveShareWeb.events import EventManager, RegistrationEvent, ListingOwnerListener, ListingRegisterListener, \
    PayerListner, PaymentEvent, PayeeListner, ReviewListner, ReviewEvent
from DriveShareWeb.orm.connect import prepare_db
from DriveShareWeb.payment import PaymentService
from DriveShareWeb.reset import PasswordResetQ1, PasswordResetCoR, PasswordResetQ2, PasswordResetQ3
from DriveShareWeb.security import password
from DriveShareWeb.security.password import hash_password
from DriveShareWeb.security.token import Token, create_access_token
from DriveShareWeb.orm.model import Account, AccountDTO, NewListingDTO, Listing, AvailableDateRange, ExistingListingDTO, \
    ReservationDTO, Reservation, Review, ReviewDTO, PasswordResetDTO
from DriveShareWeb.utils import TimeRange

app = FastAPI()

app.mount("/static", StaticFiles(directory="DriveShareWeb/static"), name="static")

event_manager = EventManager()


@app.on_event("startup")
def on_startup():
    prepare_db()

    # setup event manager
    event_manager.subscribe(RegistrationEvent, ListingOwnerListener())
    event_manager.subscribe(RegistrationEvent, ListingRegisterListener())
    event_manager.subscribe(PaymentEvent, PayerListner())
    event_manager.subscribe(PaymentEvent, PayeeListner())
    event_manager.subscribe(ReviewEvent, ReviewListner())


# URL rewrite

@app.get("/", response_class=HTMLResponse)
async def home_page(account=Depends(get_current_user)):
    with open("DriveShareWeb/static/home.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


@app.get("/searchlistings", response_class=HTMLResponse)
async def home_page(account=Depends(get_current_user)):
    with open("DriveShareWeb/static/searchlistings.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


@app.get("/mylistings", response_class=HTMLResponse)
async def home_page(account=Depends(get_current_user)):
    with open("DriveShareWeb/static/mylistings.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


@app.get("/myreservations", response_class=HTMLResponse)
async def home_page(account=Depends(get_current_user)):
    with open("DriveShareWeb/static/myreservations.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


@app.get("/login", response_class=HTMLResponse)
async def login_page(not_login=Depends(ensure_user_not_logged_in)):
    with open("DriveShareWeb/static/login.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(not_login=Depends(ensure_user_not_logged_in)):
    with open("DriveShareWeb/static/signup.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


@app.get("/recover", response_class=HTMLResponse)
async def signup_page(not_login=Depends(ensure_user_not_logged_in)):
    with open("DriveShareWeb/static/recover.html") as f:
        html = f.readlines()

    return HTMLResponse(content=str.join("", html), status_code=200)


# CRUD endpoints

@app.get("/listing", response_model=list[ExistingListingDTO])
async def get_all_listings(account: Annotated[AccountDTO, Depends(get_current_user)],
                           sess: Annotated[Session, Depends(db_session)]):
    """Get all listings."""
    listings = sess.exec(select(Listing))

    out = []
    for listing in listings:
        ranges = sess.exec(select(AvailableDateRange).where(AvailableDateRange.listing_id == listing.id))
        out.append(ExistingListingDTO.from_orm_parts(listing, ranges))

    return out


@app.get("/listing/self", response_model=list[ExistingListingDTO])
async def get_owned_listings(account: Annotated[AccountDTO, Depends(get_current_user)],
                             sess: Annotated[Session, Depends(db_session)]):
    """Get all listings owned by self."""
    listings = sess.exec(select(Listing).where(Listing.owner == account.email))

    out = []
    for listing in listings:
        ranges = sess.exec(select(AvailableDateRange).where(AvailableDateRange.listing_id == listing.id))
        out.append(ExistingListingDTO.from_orm_parts(listing, ranges))

    return out


@app.get("/listing/{id}", response_model=ExistingListingDTO)
async def get_listing(id: int, account: Annotated[AccountDTO, Depends(get_current_user)],
                      sess: Annotated[Session, Depends(db_session)]):
    """Get specific listing."""
    listing = sess.get(Listing, id)

    if listing is None:
        raise HTTPException(400, "ID does not exist")

    ranges = sess.exec(select(AvailableDateRange).where(AvailableDateRange.listing_id == id))
    return ExistingListingDTO.from_orm_parts(listing, ranges)


@app.post("/listing", response_model=Listing, status_code=201)
async def create_listing(listing: NewListingDTO, account: Annotated[AccountDTO, Depends(get_current_user)],
                         sess: Annotated[Session, Depends(db_session)]):
    """Create a new listing, alongside its valid date ranges."""
    # Add IDs to models
    db_listing = Listing(owner=account.email, model=listing.model, year=listing.year, mileage=listing.mileage,
                         price=listing.price, location=listing.location)
    sess.add(db_listing)
    sess.commit()

    db_dates = [AvailableDateRange(listing_id=db_listing.id, start_date=d[0], end_date=d[1]) for d in
                listing.date_ranges]
    sess.add_all(db_dates)

    sess.commit()

    return db_listing


@app.put("/listing", status_code=200)
async def update_listing(listing: ExistingListingDTO, account: Annotated[AccountDTO, Depends(get_current_user)],
                         sess: Annotated[Session, Depends(db_session)]):
    """Updates an existing listing using the passed listing object. User must own listing."""
    old_listing = sess.get(Listing, listing.id)

    if old_listing is None:
        raise HTTPException(400, "Listing does not exist!")

    # Ensure ownership is preserved
    if old_listing.owner != account.email:
        raise HTTPException(403, "User does not own listing!")

    old_listing.model = listing.model
    old_listing.year = listing.year
    old_listing.mileage = listing.mileage
    old_listing.price = listing.price
    old_listing.location = listing.location

    sess.add(old_listing)

    # Get existing dates, and just delete them
    old_dates = sess.exec(select(AvailableDateRange).where(AvailableDateRange.listing_id == listing.id))
    for date in old_dates:
        sess.delete(date)

    # Just add all dates as new for simplicity
    new_dates = [AvailableDateRange(listing_id=listing.id, start_date=d[0], end_date=d[1]) for d in
                 listing.date_ranges]
    sess.add_all(new_dates)

    sess.commit()


@app.get("/reservation", response_model=list[Reservation])
async def get_own_reservations(account: Annotated[AccountDTO, Depends(get_current_user)],
                               sess: Annotated[Session, Depends(db_session)]):
    """Get all reservations owned by self."""

    res = sess.exec(select(Reservation).where(Reservation.owner == account.email))

    return res


@app.get("/reservation/self", response_model=list[Reservation])
async def get_listing_reservations(account: Annotated[AccountDTO, Depends(get_current_user)],
                                   sess: Annotated[Session, Depends(db_session)]):
    """Get all reservations for listings owned by self."""

    res = sess.exec(
        select(Reservation).join(Listing).where(Listing.owner == account.email))

    return res


@app.get("/reservation/{id}", response_model=list[Reservation])
async def get_reservation_for_listing(id: int,
                                      account: Annotated[AccountDTO, Depends(get_current_user)],
                                      sess: Annotated[Session, Depends(db_session)]):
    """Get all reservations for a given listing"""

    res = sess.exec(
        select(Reservation).join(Listing).where(Listing.id == id))

    return res


@app.post("/reservation", response_model=Reservation, status_code=201)
async def create_reservation(reservation: ReservationDTO, account: Annotated[AccountDTO, Depends(get_current_user)],
                             sess: Annotated[Session, Depends(db_session)]):
    """Attempts to create a new reservation for a listing."""

    listing = sess.get(Listing, reservation.listing_id)

    if listing is None:
        raise HTTPException(400, "Listing does not exist")

    if listing.owner == account.email:
        raise HTTPException(400, "Cannot reserve own listing!")

    # Check if reservation is valid for listing
    dates = sess.exec(select(AvailableDateRange).where(AvailableDateRange.listing_id == listing.id))

    if dates is None:
        raise HTTPException(400, "Listing has no available dates!")

    og_ranges = [TimeRange(r[0], r[1]) for r in reduce(lambda x, y: x + y, [d.to_ranges() for d in dates])]

    existing_reservations = sess.exec(select(Reservation).where(Reservation.listing_id == listing.id))
    existing_reservations = [TimeRange(d.start_date, d.end_date) for d in existing_reservations]

    new_range = TimeRange(reservation.start_date, reservation.end_date)

    # First see if new range fits in any old range
    found = False
    for range in og_ranges:
        found |= new_range.start >= range.start and new_range.end <= range.end

    if not found:
        raise HTTPException(400, "Reservation is not in listing time range!")

    # Next see if it overlaps with any existing reservations. If this occurs, then it cannot be valid
    found = False
    for range in existing_reservations:
        found |= new_range.is_overlapped(range)

    if found:
        raise HTTPException(400, "Reservation range overlaps with existing reservation!")

    # Reservation is good, save to db
    res = Reservation(owner=account.email, **reservation.model_dump())
    sess.add(res)
    sess.commit()

    event_manager.publish(RegistrationEvent(listing, res))

    return res


@app.get("/review/{id}", response_model=list[Review])
async def get_reviews_for_listing(id: int, account: Annotated[AccountDTO, Depends(get_current_user)],
                                  sess: Annotated[Session, Depends(db_session)]):
    """Get all reviews for a given reservation"""

    res = sess.exec(
        select(Review).join(Reservation).where(Reservation.id == id))

    return res


@app.post("/review", response_model=Review, status_code=201)
async def create_review(review: ReviewDTO, account: Annotated[AccountDTO, Depends(get_current_user)],
                        sess: Annotated[Session, Depends(db_session)]):
    """Create a review for a reservation you submitted, or is for a listing you own."""

    reservation = sess.get(Reservation, review.reservation_id)
    listing = sess.get(Listing, reservation.listing_id)

    if reservation is None:
        raise HTTPException(400, "Reservation did not exist!")

    if account.email != reservation.owner and listing.owner != account.email:
        raise HTTPException(403, "Cannot review a reservation that is not yours!")

    db_review = Review(owner=account.email, **review.model_dump())
    sess.add(db_review)
    sess.commit()

    event_manager.publish(ReviewEvent(db_review, listing))

    return db_review


@app.post("/payment")
async def submit_payment(reservation: Reservation, account: Annotated[AccountDTO, Depends(get_current_user)],
                         payment_service: Annotated[PaymentService, Depends(get_payment_service)],
                         sess: Annotated[Session, Depends(db_session)]):
    """Submits payment for a reservation."""

    listing = sess.get(Listing, reservation.listing_id)

    if account.email != reservation.owner:
        raise HTTPException(403, "You can only pay for our own reservation")

    # Calculate price
    price = listing.price * (datetime.date.fromisoformat(reservation.end_date) - datetime.date.fromisoformat(
        reservation.start_date)).days

    # Handle payment
    payment_service.handle_payment(price)

    event_manager.publish(PaymentEvent(listing, reservation, price))


@app.post("/payment/query", response_model=float)
async def get_payment(reservation: Reservation, account: Annotated[AccountDTO, Depends(get_current_user)],
                      sess: Annotated[Session, Depends(db_session)]):
    """Get a reservations price."""

    listing = sess.get(Listing, reservation.listing_id)

    if account.email != reservation.owner:
        raise HTTPException(403, "You can only pay for our own reservation")

    # Calculate price
    price = listing.price * (datetime.date.fromisoformat(reservation.end_date) - datetime.date.fromisoformat(
        reservation.start_date)).days

    return price


# Login

@app.post("/signup")
async def signup(username: Annotated[str, Form()], password: Annotated[str, Form()],
                 seq1: Annotated[str, Form()],
                 seq2: Annotated[str, Form()],
                 seq3: Annotated[str, Form()],
                 sess: Annotated[Session, Depends(db_session)],
                 not_login=Depends(ensure_user_not_logged_in)):
    """Creates a new user account"""
    existing_acc = sess.get(Account, username)

    if existing_acc:
        raise HTTPException(400, "A user with that email already exists!")

    new_acc = Account(email=username, password=hash_password(password), secq1=seq1, secq2=seq2, secq3=seq3)
    sess.add(new_acc)
    sess.commit()


@app.post("/passwordreset")
async def password_reset(details: PasswordResetDTO, account: Annotated[AccountDTO, Depends(get_current_user)],
                         session: Annotated[Session, Depends(db_session)]):
    """
    Resets the password for a signed-in user. Requires the submission of answers to 3 security questions, which will
    be checked.
    """
    account = session.get(Account, account.email)

    # Makes type system happy, since we know account must exist
    assert isinstance(account, Account)

    cor = PasswordResetQ1(account)
    cor2 = PasswordResetQ2(account)
    cor3 = PasswordResetQ3(account)
    cor.add_next(cor2)
    cor2.add_next(cor3)

    # Ensure answers are correct
    res = cor.handle(details)

    if res:
        # Update password
        account.password = hash_password(details.new_password)
        session.add(account)
        session.commit()
    else:
        raise HTTPException(400, "Password recovery questions incorrect!")


@app.post("/token", response_model=Token)
async def create_token(
        form: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response
):
    """Creates an OAuth2 token"""
    if password.verify_password(form.password, form.username):
        access_token = create_access_token(form.username)
        # Set token in cookie and respond as JSON
        response.set_cookie("access_token", f"bearer {access_token}", httponly=True)
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/logout")
async def logout():
    """Destroys the login token"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response
