## Event Observer

```mermaid
classDiagram
    direction RL
    class Event {
    }

    class RegistrationEvent {
        + listing: Listing
        + reg: Registration
    }

    class PaymentEvent {
        + reg: Registration
        + listing: Listing
        + price: float
    }

    class ReviewEvent {
        + review: Review
        + listing: Listing
    }

    class EventManager {
        - listeners: Map~Event, List[EventListener]~
        + subscribe(Event, EventListener)
        + publish(Event)
    }

    class EventListener {
        <<interface>>
        + update(Event)
    }

    class ListingOwnerListener {
        + update(Event)
    }

    class ListingRegisterListener {
        + update(Event)
    }

    class PayeeListener {
        + update(Event)
    }

    class PayerListener {
        + update(Event)
    }

    class ReviewListener {
        + update(Event)
    }

    Event <|-- RegistrationEvent
    Event <|-- PaymentEvent
    Event <|-- ReviewEvent
    EventListener <|-- ListingOwnerListener
    EventListener <|-- ListingRegisterListener
    EventListener <|-- PayeeListener
    EventListener <|-- PayerListener
    EventListener <|-- ReviewListener
    ListingOwnerListener -- RegistrationEvent
    ListingRegisterListener -- RegistrationEvent
    PayeeListener -- PaymentEvent
    PayerListener -- PaymentEvent
    ReviewListener -- ReviewEvent
    EventManager *-- EventListener
```

We create an event system that allows for subscribing to events created in the backend. This is designed to be used for
notifying users, however it could be used for other functionality if required.

This is implemented in events.py.

## Payment Proxy

```mermaid
classDiagram
    direction TB
    class PaymentService {
        <<interface>>
        + handle_payment(price: float)
    }

    class MockPaymentService {
        + handle_payment(price: float)
    }

    class LoggerPaymentProxy {
        - wrapped: PaymentService
        + handle_payment(price: float)
    }

    PaymentService <|-- MockPaymentService
    PaymentService <|-- LoggerPaymentProxy
    LoggerPaymentProxy *-- PaymentService
```

The payment system is implemented as a mock with a proxy for logging. The mock takes the place
of an actual payment handler, and simply does nothing. The logger proxy wraps this mock (or a real
service), and simply logs the action in the server before performing the wrapped services transaction.

## Password Reset CoR

```mermaid
classDiagram
    class PasswordResetCoR {
        <<abstract>>
        - next: PasswordResetCoR
        + add_next(handler: PasswordResetCoR)
        + handle(request: PasswordResetDTO) bool
    }

    class PasswordResetQ1
    class PasswordResetQ2
    class PasswordResetQ3

    PasswordResetCoR *-- PasswordResetCoR
    PasswordResetCoR <|-- PasswordResetQ1
    PasswordResetCoR <|-- PasswordResetQ2
    PasswordResetCoR <|-- PasswordResetQ3
```

The password Chain of Responsibility works as one would think, returning
false early if any question fails, or true otherwise.
