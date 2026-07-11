from __future__ import annotations

import math
import unittest

from llm_sr_benchmark.metrics import (
    ConfusionMatrix,
    cohen_kappa_from_cm,
    confusion_matrix,
    fleiss_kappa_binary,
    performance,
)


class MetricTests(unittest.TestCase):
    def test_confusion_matrix(self) -> None:
        observed = confusion_matrix(
            [True, True, False, False],
            [True, False, True, False],
        )
        self.assertEqual(observed, ConfusionMatrix(tp=1, fp=1, fn=1, tn=1))

    def test_perfect_kappa(self) -> None:
        self.assertEqual(cohen_kappa_from_cm(ConfusionMatrix(4, 0, 0, 6)), 1.0)

    def test_known_sr1_title_kappa(self) -> None:
        value = cohen_kappa_from_cm(ConfusionMatrix(218, 17, 278, 1043))
        self.assertTrue(math.isclose(value, 0.4924119444972775, rel_tol=0, abs_tol=1e-15))

    def test_performance(self) -> None:
        values = performance(ConfusionMatrix(27, 43, 1, 15))
        self.assertTrue(math.isclose(values["Sensitivity_pct"], 96.42857142857143))
        self.assertTrue(math.isclose(values["Specificity_pct"], 25.862068965517242))

    def test_fleiss_perfect_agreement(self) -> None:
        value = fleiss_kappa_binary(
            [[True, False, True], [True, False, True], [True, False, True]]
        )
        self.assertEqual(value, 1.0)


if __name__ == "__main__":
    unittest.main()

