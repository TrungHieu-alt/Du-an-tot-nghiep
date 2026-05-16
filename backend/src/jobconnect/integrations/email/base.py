from __future__ import annotations

from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    def send(self, to_email: str, subject: str, body: str) -> None:
        """Attempt to send an email. Must not raise — implementations log
        failures internally and return normally."""
