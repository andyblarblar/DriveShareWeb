from .orm.model import Reservation, Listing, Review
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import defaultdict
from email.message import EmailMessage


def construct_email(body: str, subject: str, to_addr: str) -> EmailMessage:
    mess = EmailMessage()
    mess['From'] = "donotreply@driveshareweb.com"
    mess['To'] = to_addr
    mess['Subject'] = subject

    mess.set_content(body)
    return mess


class Event:
    """Base class of the event system. Should be introspected in a match statement."""
    pass


@dataclass
class RegistrationEvent(Event):
    """Event fired when a reservation is created or changed."""
    listing: Listing
    reservation: Reservation


@dataclass
class PaymentEvent(Event):
    """Event fired when a reservation is paid for."""
    listing: Listing
    reservation: Reservation
    price: float


@dataclass
class ReviewEvent(Event):
    """Event fired when a review is submitted."""
    review: Review
    listing: Listing


class EventListener(ABC):
    @abstractmethod
    def update(self, event: Event):
        ...


class ListingRegisterListener(EventListener):
    """Handles notifying the create of a reservation."""

    def update(self, event: Event):
        event: RegistrationEvent

        message = f"Your reservation: {event.reservation.id} for {event.reservation.start_date} has been confirmed."

        email = construct_email(message, "Reservation conformation", event.reservation.owner)

        print(str(email))


class ListingOwnerListener(EventListener):
    """Handles notifying the owner of a listing, when they get a new reservation."""

    def update(self, event: Event):
        event: RegistrationEvent

        message = f"Your listing: {event.listing.id} has a new reservation from {event.reservation.owner} on {event.reservation.start_date}"

        email = construct_email(message, "Reservation conformation", event.listing.owner)

        print(str(email))


class PayerListner(EventListener):
    """Handles notifying the payer of their order."""

    def update(self, event: Event):
        event: PaymentEvent

        message = f"Your payment of ${event.price} has been confirmed."

        email = construct_email(message, "Payment confirmation", event.reservation.owner)

        print(str(email))


class PayeeListner(EventListener):
    """Handles notifying the owner of a listing, when a payment occurs."""

    def update(self, event: Event):
        event: PaymentEvent

        message = f"Your client has sent ${event.price} for your reservation."

        email = construct_email(message, "Payment confirmation", event.listing.owner)

        print(str(email))


class ReviewListner(EventListener):
    """Handles notifying the owner of a listing when a review is submitted."""

    def update(self, event: Event):
        event: ReviewEvent

        message = f"Your listing {event.listing.id} has received a review! \n '{event.review.text}'"

        email = construct_email(message, "Review submitted", event.listing.owner)

        print(str(email))


class EventManager:
    """Manages listeners and events throughout the system."""

    def __init__(self):
        self._listeners: defaultdict[type, list[EventListener]] = defaultdict(list)

    def subscribe(self, event: type, listener: EventListener):
        """Add a listener that fires for a particular event. Event should be the class of the Event to listen on."""
        self._listeners[event] += [listener]

    def publish(self, event: Event):
        """Dispatch an event, firing subscribers. This is blocking."""
        # Dispatch event to subscribers
        for listener in self._listeners[type(event)]:
            listener.update(event)
