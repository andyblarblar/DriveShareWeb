from abc import ABC, abstractmethod
import logging


class PaymentService(ABC):
    """Objects that can handle customer payment."""

    @abstractmethod
    def handle_payment(self, price: float):
        """Handles customer payment."""
        ...


class MockPaymentService(PaymentService):
    """Simply payment mock that does nothing."""

    def handle_payment(self, price: float):
        pass


class LoggerPaymentProxy(PaymentService):
    """Proxy that does logging before calling the wrapped service."""

    def __init__(self, wrapped: PaymentService):
        self._wrapped = wrapped

    def handle_payment(self, price: float):
        logging.info(f"Submitting payment of ${price}")
        self._wrapped.handle_payment(price)
