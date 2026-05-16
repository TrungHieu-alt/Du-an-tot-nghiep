from __future__ import annotations

import os

from jobconnect.integrations.email.base import EmailSender


def get_email_sender() -> EmailSender:
    """Return the configured email sender.

    EMAIL_PROVIDER env var selects the backend (default: local).
    Only 'local' is implemented for MVP; add 'smtp' or 'sendgrid' here later.
    """
    provider = os.getenv("EMAIL_PROVIDER", "local").lower()
    if provider == "local":
        from jobconnect.integrations.email.local import LocalLogEmailSender
        return LocalLogEmailSender()
    raise ValueError(f"Unknown EMAIL_PROVIDER: {provider!r}")
