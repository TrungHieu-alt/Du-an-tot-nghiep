from __future__ import annotations

import logging

from jobconnect.integrations.email.base import EmailSender

logger = logging.getLogger(__name__)


class LocalLogEmailSender(EmailSender):
    """Dev/test sender: writes email content to the application log."""

    def send(self, to_email: str, subject: str, body: str) -> None:
        logger.info("EMAIL [local] to=%s subject=%r body=%r", to_email, subject, body[:200])
