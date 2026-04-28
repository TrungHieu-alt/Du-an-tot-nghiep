import threading
import time
import unittest

from ragmodel.logics.gemini_job_queue import GeminiJobQueue


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, handler):
        self._handler = handler

    def generate_content(self, model, contents):
        return self._handler(model, contents)


class _FakeClient:
    def __init__(self, handler):
        self.models = _FakeModels(handler)


class GeminiJobQueueTests(unittest.TestCase):
    def test_submit_success_returns_trimmed_text(self):
        client = _FakeClient(lambda _m, _c: _FakeResponse("  ok  "))
        q = GeminiJobQueue(client=client, workers=1, maxsize=10, retries=0)

        out = q.submit(model="x", prompt="hello", timeout_sec=1.0)

        self.assertEqual(out, "ok")


    def test_submit_times_out_when_queue_is_full(self):
        release = threading.Event()

        def slow_handler(_m, _c):
            release.wait(timeout=1.0)
            return _FakeResponse("late")

        client = _FakeClient(slow_handler)
        q = GeminiJobQueue(client=client, workers=1, maxsize=1, retries=0)

        # First job occupies the worker.
        t1 = threading.Thread(
            target=lambda: q.submit(model="x", prompt="first", timeout_sec=1.0), daemon=True
        )
        t1.start()
        time.sleep(0.05)
        # Second job fills the queue.
        t2 = threading.Thread(
            target=lambda: q.submit(model="x", prompt="second", timeout_sec=1.0), daemon=True
        )
        t2.start()
        time.sleep(0.05)

        # Third enqueue should fail quickly due to full queue.
        with self.assertRaises(TimeoutError) as ctx:
            q.submit(model="x", prompt="third", timeout_sec=0.05)
        self.assertIn("full", str(ctx.exception).lower())
        release.set()


    def test_submit_times_out_waiting_for_worker_completion(self):
        def very_slow_handler(_m, _c):
            time.sleep(0.5)
            return _FakeResponse("slow")

        client = _FakeClient(very_slow_handler)
        q = GeminiJobQueue(client=client, workers=1, maxsize=10, retries=0)

        with self.assertRaises(TimeoutError) as ctx:
            q.submit(model="x", prompt="slow-job", timeout_sec=0.05)
        self.assertIn("waiting for worker", str(ctx.exception).lower())
