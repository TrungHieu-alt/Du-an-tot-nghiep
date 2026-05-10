import unittest

from db_v2.validate_scenario_dataset import validate_dataset


class MatchingV2ScenarioDatasetTests(unittest.TestCase):
    def test_slice_6b_scenario_dataset_validation_passes(self):
        summary = validate_dataset()

        self.assertEqual(summary["jobs"], 6)
        self.assertEqual(summary["candidates"], 36)
        self.assertEqual(summary["job_embeddings"], 6)
        self.assertEqual(summary["candidate_embeddings"], 35)
        self.assertEqual(summary["in_memory_expectations"]["passed"], 8)
        self.assertEqual(summary["in_memory_expectations"]["total"], 8)
        self.assertEqual(
            summary["embedding_hash"],
            "82f869e8b8def9d316a10aadd966e555979dd5acc468c0d86524d19e47f77ec9",
        )


if __name__ == "__main__":
    unittest.main()
