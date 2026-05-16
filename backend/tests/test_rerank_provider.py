from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.integrations.rerank import (
    LocalCrossEncoderRerankProvider,
    RerankError,
    get_rerank_provider,
    reset_rerank_provider_cache,
)


class RerankProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._snap = dict(os.environ)
        reset_rerank_provider_cache()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._snap)
        reset_rerank_provider_cache()

    def test_factory_returns_local_provider(self) -> None:
        provider = get_rerank_provider()
        self.assertIsInstance(provider, LocalCrossEncoderRerankProvider)

    def test_score_clamps_to_zero_one(self) -> None:
        provider = LocalCrossEncoderRerankProvider(model_name="dummy-model")
        with patch("jobconnect.integrations.rerank.local._load_model") as mock_model_loader:
            mock_model_loader.return_value.predict.return_value = [-2.0, 0.5, 5.0]
            result = provider.score("query", ["a", "b", "c"])
        self.assertEqual(result, [0.0, 0.5, 1.0])

    def test_score_raises_rerank_error_on_model_failure(self) -> None:
        provider = LocalCrossEncoderRerankProvider(model_name="dummy-model")
        with patch("jobconnect.integrations.rerank.local._load_model", side_effect=RuntimeError("boom")):
            with self.assertRaises(RerankError):
                provider.score("query", ["doc"])


if __name__ == "__main__":
    unittest.main()
