import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class _QueueJob:
    model: str
    prompt: str
    done_event: threading.Event
    result: Optional[str] = None
    error: Optional[Exception] = None


class GeminiJobQueue:
    def __init__(
        self,
        client: Any,
        workers: int,
        maxsize: int,
        retries: int,
    ) -> None:
        self._client = client
        self._retries = max(0, retries)
        self._queue: "queue.Queue[_QueueJob]" = queue.Queue(maxsize=maxsize)
        self._workers = []
        for _ in range(max(1, workers)):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)

    def submit(self, model: str, prompt: str, timeout_sec: float) -> str:
        job = _QueueJob(model=model, prompt=prompt, done_event=threading.Event())
        try:
            self._queue.put(job, timeout=timeout_sec)
        except queue.Full as exc:
            raise TimeoutError("Gemini queue is full; request could not be enqueued") from exc

        if not job.done_event.wait(timeout=timeout_sec):
            raise TimeoutError(
                f"Gemini job exceeded timeout while waiting for worker ({timeout_sec}s)"
            )

        if job.error is not None:
            raise job.error
        if job.result is None:
            raise RuntimeError("Gemini job completed without a result")
        return job.result

    def _worker_loop(self) -> None:
        while True:
            job = self._queue.get()
            try:
                job.result = self._run_with_retries(job.model, job.prompt)
            except Exception as exc:  # pragma: no cover
                job.error = exc
            finally:
                job.done_event.set()
                self._queue.task_done()

    def _run_with_retries(self, model: str, prompt: str) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(self._retries + 1):
            try:
                response = self._client.models.generate_content(model=model, contents=prompt)
                text = getattr(response, "text", None)
                if text is None:
                    raise ValueError("Gemini response did not include text output")
                return text.strip()
            except Exception as exc:  # pragma: no cover
                last_error = exc
                if attempt >= self._retries:
                    break
                time.sleep(0.4 * (attempt + 1))

        raise last_error if last_error is not None else RuntimeError("Unknown Gemini error")
