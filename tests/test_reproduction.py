from __future__ import annotations

import csv
import math
from pathlib import Path
import tempfile
import unittest

from llm_sr_benchmark.analysis import reproduce
from llm_sr_benchmark.validation import EXPECTATIONS, validate_all, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "locked"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReproductionTests(unittest.TestCase):
    def test_locked_denominators(self) -> None:
        self.assertEqual(validate_all(DATA), [])
        for review, expectation in EXPECTATIONS.items():
            errors, summary = validate_dataset(review, DATA)
            self.assertEqual(errors, [], summary)
            self.assertIn(f"records={expectation.records}", summary)

    def test_publication_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            actual = Path(temporary)
            reproduce(DATA, actual)
            for filename in (
                "table1_validity.csv",
                "table2_agreement.csv",
                "heterogeneity.csv",
            ):
                expected_rows = read_csv(ROOT / "results" / "published" / filename)
                actual_rows = read_csv(actual / filename)
                self.assertEqual(len(actual_rows), len(expected_rows), filename)
                self.assertEqual(actual_rows[0].keys(), expected_rows[0].keys(), filename)
                for expected, observed in zip(expected_rows, actual_rows, strict=True):
                    for field in expected:
                        try:
                            expected_number = float(expected[field])
                            observed_number = float(observed[field])
                        except ValueError:
                            self.assertEqual(observed[field], expected[field], (filename, field))
                        else:
                            self.assertTrue(
                                math.isclose(
                                    observed_number,
                                    expected_number,
                                    rel_tol=1e-12,
                                    abs_tol=1e-12,
                                ),
                                (filename, field, expected_number, observed_number),
                            )

    def test_locked_confusion_matrices(self) -> None:
        expected = [
            ("SR1", "Model 1 (TF)", "Title screening", "ChatGPT", 1556, 218, 17, 278, 1043),
            ("SR1", "Model 1 (TF)", "Title screening", "Gemini", 1556, 115, 7, 381, 1053),
            ("SR1", "Model 1 (TF)", "Title/abstract screening", "ChatGPT", 496, 72, 164, 14, 246),
            ("SR1", "Model 1 (TF)", "Title/abstract screening", "Gemini", 496, 44, 53, 42, 357),
            ("SR1", "Model 1 (TF)", "Full-text inclusion", "ChatGPT", 86, 27, 43, 1, 15),
            ("SR1", "Model 1 (TF)", "Full-text inclusion", "Gemini", 86, 21, 25, 7, 33),
            ("SR1", "Model 2 (nTF)", "Final inclusion", "ChatGPT", 1556, 25, 127, 3, 1401),
            ("SR1", "Model 2 (nTF)", "Final inclusion", "Gemini", 1556, 12, 43, 16, 1485),
            ("SR1", "One-shot (exploratory)", "Full-text inclusion", "ChatGPT", 1556, 26, 336, 2, 1192),
            ("SR1", "One-shot (exploratory)", "Full-text inclusion", "Gemini", 1556, 20, 113, 8, 1415),
            ("SR2", "Model 2 (nTF)", "Final inclusion", "ChatGPT", 3720, 73, 206, 1, 3440),
            ("SR2", "Model 2 (nTF)", "Final inclusion", "Gemini", 3720, 59, 133, 15, 3513),
            ("SR3", "Model 1 (TF)", "Title/abstract screening", "ChatGPT", 746, 101, 229, 0, 416),
            ("SR3", "Model 1 (TF)", "Title/abstract screening", "Gemini", 746, 95, 211, 6, 434),
            ("SR3", "Model 1 (TF)", "Full-text inclusion", "ChatGPT", 101, 50, 22, 10, 19),
            ("SR3", "Model 1 (TF)", "Full-text inclusion", "Gemini", 101, 51, 24, 9, 17),
            ("SR3", "Model 2 (nTF)", "Final inclusion", "ChatGPT", 746, 50, 116, 10, 570),
            ("SR3", "Model 2 (nTF)", "Final inclusion", "Gemini", 746, 51, 91, 9, 595),
        ]
        rows = read_csv(ROOT / "results" / "published" / "table1_validity.csv")
        observed = [
            (
                row["Review"], row["Model"], row["Endpoint"], row["LLM"],
                int(row["N"]), int(row["TP"]), int(row["FP"]),
                int(row["FN"]), int(row["TN"]),
            )
            for row in rows
        ]
        self.assertEqual(observed, expected)

    def test_locked_missing_output_counts(self) -> None:
        expected = [
            51, 1, 0, 0, 0, 0, 11, 2, 139, 107,
            0, 963, 3, 3, 25, 22, 133, 146,
        ]
        rows = read_csv(ROOT / "results" / "published" / "table1_validity.csv")
        self.assertEqual(
            [int(row["Model_missing_outputs"]) for row in rows],
            expected,
        )


if __name__ == "__main__":
    unittest.main()
