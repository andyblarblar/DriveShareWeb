from .orm.model import Reservation, Listing, Review
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import defaultdict


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


@dataclass
class ReviewEvent(Event):
    """Event fired when a review is submitted."""
    review: Review
    reservation: Reservation


class EventListener(ABC):
    @abstractmethod
    def update(self, event: Event):
        ...


class ListingRegisterListener(EventListener):
    """Handles notifying the create of a reservation."""
    pass  # TODO


class ListingOwnerListener(EventListener):
    """Handles notifying the owner of a listing, when they get a new reservation."""
    pass  # TODO


class PayerListner(EventListener):
    """Handles notifying the payer of their order."""
    pass  # TODO


class PayeeListner(EventListener):
    """Handles notifying the owner of a listing, when a payment occurs."""
    pass  # TODO


class ReviewListner(EventListener):
    """Handles notifying the owner of a listing when a review is submitted."""
    pass  # TODO


class EventManager:
    def __init__(self):
        self._listeners: defaultdict[type, list[EventListener]] = defaultdict(list)

    def subscribe(self, event: type, listener: EventListener):
        self._listeners[event] += listener

    def publish(self, event: Event):
        # Dispatch event to subscribers
        for listener in self._listeners[type(event)]:
            listener.update(event)
