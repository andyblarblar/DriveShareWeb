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
    }

    class ReviewEvent {
        + review: Review
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