import logging
from typing import Optional


def is_quota_limit_error(error: Exception) -> bool:
    text = f"{type(error).__name__}: {error}".lower()
    markers = (
        "quota",
        "resource_exhausted",
        "429",
        "rate limit",
        "ratelimit",
        "too many requests",
    )
    return any(marker in text for marker in markers)


def log_quota_limit_if_detected(
    logger: logging.Logger,
    error: Exception,
    stage: str,
    model: Optional[str] = None,
) -> bool:
    if not is_quota_limit_error(error):
        return False

    model_part = f", model={model}" if model else ""
    logger.error(
        "Gemini quota limit reached at stage=%s%s. API key may be out of quota or rate-limited. error=%s",
        stage,
        model_part,
        error,
    )
    return True
