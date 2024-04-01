from abc import ABC, abstractmethod
from typing import Optional

from DriveShareWeb.orm.model import PasswordResetDTO, Account


class PasswordResetCoR(ABC):
    def __init__(self):
        self._next: Optional[PasswordResetCoR] = None

    def add_next(self, handler: "PasswordResetCoR"):
        self._next = handler

    @abstractmethod
    def handle(self, answers: PasswordResetDTO) -> bool:
        """Handles the request to reset password. Returns True if it is ok to update the password."""
        ...


class PasswordResetQ1(PasswordResetCoR):
    """Handles validating the first password reset question"""
    def __init__(self, record: Account):
        super().__init__()
        self._answer = record.secq1

    def handle(self, answers: PasswordResetDTO) -> bool:

        child = self._next.handle(answers) if self._next else None

        if child is not None and not child:
            return child
        else:
            return self._answer == answers.q1


class PasswordResetQ2(PasswordResetCoR):
    """Handles validating the second password reset question"""
    def __init__(self, record: Account):
        super().__init__()
        self._answer = record.secq2

    def handle(self, answers: PasswordResetDTO) -> bool:
        child = self._next.handle(answers) if self._next else None

        if child is not None and not child:
            return child
        else:
            return self._answer == answers.q2


class PasswordResetQ3(PasswordResetCoR):
    """Handles validating the third password reset question"""
    def __init__(self, record: Account):
        super().__init__()
        self._answer = record.secq3

    def handle(self, answers: PasswordResetDTO) -> bool:
        child = self._next.handle(answers) if self._next else None

        if child is not None and not child:
            return child
        else:
            return self._answer == answers.q3
