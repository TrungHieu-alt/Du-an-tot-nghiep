"""Email sender adapter boundary.

The default adapter is local/log-only so development and tests never require
network access or provider credentials. A provider-backed SMTP sender can be
enabled through env vars without changing business services.
"""
from __future__ import annotations

import logging
import os
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage as SMTPEmailMessage
from functools import lru_cache
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailSendResult:
    status: str
    provider: str
    provider_message_id: Optional[str] = None


class EmailSendError(Exception):
    """Raised by an email adapter when delivery cannot complete."""

    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(message)
        self.provider = provider


class EmailSender(Protocol):
    provider_name: str

    def send_email(
        self,
        to: Optional[str],
        subject: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EmailSendResult:
        """Send or log an email attempt."""


@dataclass
class LocalLogEmailSender:
    """Development/test sender that records intent without real delivery."""

    provider_name: str = "local"
    sent_messages: list[dict[str, Any]] = field(default_factory=list)

    def send_email(
        self,
        to: Optional[str],
        subject: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EmailSendResult:
        self.sent_messages.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "metadata": metadata or {},
            }
        )
        logger.info("Logged local email to=%s subject=%r", to, subject)
        return EmailSendResult(status="logged", provider=self.provider_name)


@dataclass(frozen=True)
class SmtpEmailSender:
    host: str
    port: int
    from_email: str
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    timeout_seconds: float = 5.0
    provider_name: str = "smtp"

    def send_email(
        self,
        to: Optional[str],
        subject: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EmailSendResult:
        if not to:
            raise EmailSendError("Recipient email is missing.", provider=self.provider_name)

        message = SMTPEmailMessage()
        message["From"] = self.from_email
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as smtp:
                if self.use_tls:
                    smtp.starttls()
                if self.username:
                    smtp.login(self.username, self.password or "")
                smtp.send_message(message)
        except Exception as exc:
            raise EmailSendError(str(exc), provider=self.provider_name) from exc

        return EmailSendResult(status="sent", provider=self.provider_name)


def _smtp_sender_from_env() -> Optional[SmtpEmailSender]:
    host = os.getenv("SMTP_HOST", "").strip()
    from_email = os.getenv("EMAIL_FROM", "").strip()
    if not host or not from_email:
        return None

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        port = 587

    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no"}
    try:
        timeout_seconds = max(1.0, float(os.getenv("SMTP_TIMEOUT_SECONDS", "5")))
    except ValueError:
        timeout_seconds = 5.0

    return SmtpEmailSender(
        host=host,
        port=port,
        from_email=from_email,
        username=os.getenv("SMTP_USERNAME", "").strip() or None,
        password=os.getenv("SMTP_PASSWORD", ""),
        use_tls=use_tls,
        timeout_seconds=timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_email_sender() -> EmailSender:
    provider = os.getenv("EMAIL_PROVIDER", "local").strip().lower()
    if provider in {"local", "log", ""}:
        return LocalLogEmailSender()
    if provider == "smtp":
        sender = _smtp_sender_from_env()
        if sender is not None:
            return sender
        logger.warning(
            "EMAIL_PROVIDER=smtp but SMTP_HOST or EMAIL_FROM is missing; falling back to local email sender."
        )
        return LocalLogEmailSender()

    logger.warning("Unknown EMAIL_PROVIDER=%r; falling back to local email sender.", provider)
    return LocalLogEmailSender()


def reset_email_sender_cache() -> None:
    """Test helper: clear the cached adapter so env overrides take effect."""

    get_email_sender.cache_clear()


__all__ = [
    "EmailSendError",
    "EmailSendResult",
    "EmailSender",
    "LocalLogEmailSender",
    "SmtpEmailSender",
    "get_email_sender",
    "reset_email_sender_cache",
]
