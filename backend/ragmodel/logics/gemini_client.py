from ragmodel.config import (
    GEMINI_API_KEY,
    GEMINI_QUEUE_MAXSIZE,
    GEMINI_QUEUE_RETRIES,
    GEMINI_QUEUE_TIMEOUT_SEC,
    GEMINI_QUEUE_WORKERS,
    MODEL,
)
from ragmodel.logics.gemini_job_queue import GeminiJobQueue

try:
    from google import genai
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "google-genai is required. Install it in backend requirements."
    ) from exc


_client = genai.Client(api_key=GEMINI_API_KEY)
_queue = GeminiJobQueue(
    client=_client,
    workers=GEMINI_QUEUE_WORKERS,
    maxsize=GEMINI_QUEUE_MAXSIZE,
    retries=GEMINI_QUEUE_RETRIES,
)


def generate_text(prompt: str, model: str = MODEL) -> str:
    return _queue.submit(model=model, prompt=prompt, timeout_sec=GEMINI_QUEUE_TIMEOUT_SEC)
