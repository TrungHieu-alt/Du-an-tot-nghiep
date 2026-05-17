from __future__ import annotations

import unittest

from db.seeds.slice6d import (
    JOB_COUNT,
    LABELS,
    RESUME_COUNT,
    Slice6DConfig,
    generate_dataset,
    validate_preseed_dataset,
)


class SeedSlice6DFactoryTests(unittest.TestCase):
    def test_dataset_shape_and_ids(self) -> None:
        dataset = generate_dataset(Slice6DConfig(seed=20260517))
        jobs = dataset["jobs"]
        resumes = dataset["resumes"]
        matrix = dataset["matrix"]

        self.assertEqual(len(jobs), JOB_COUNT)
        self.assertEqual(len(resumes), RESUME_COUNT)
        self.assertEqual(len(matrix), RESUME_COUNT)
        self.assertEqual(sorted(j["job_id"] for j in jobs), list(range(2101, 2141)))
        self.assertEqual(sorted(r["resume_id"] for r in resumes), list(range(11001, 11241)))

    def test_each_job_has_six_unique_labels(self) -> None:
        dataset = generate_dataset(Slice6DConfig(seed=20260517))
        labels_by_job: dict[int, set[str]] = {}
        for item in dataset["matrix"]:
            labels_by_job.setdefault(item["job_id"], set()).add(item["design_label"])
        self.assertEqual(len(labels_by_job), JOB_COUNT)
        for labels in labels_by_job.values():
            self.assertEqual(labels, set(LABELS))

    def test_preseed_validation_passes(self) -> None:
        dataset = generate_dataset(Slice6DConfig(seed=20260517))
        errors = validate_preseed_dataset(dataset)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
