"""Dependency-free binary classification and agreement metrics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ConfusionMatrix:
    """Binary confusion matrix with the human decision as reference."""

    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    def as_dict(self) -> dict[str, int]:
        return {"TP": self.tp, "FP": self.fp, "FN": self.fn, "TN": self.tn}


def confusion_matrix(truth: Iterable[bool], prediction: Iterable[bool]) -> ConfusionMatrix:
    """Return TP, FP, FN, and TN for paired binary decisions."""

    tp = fp = fn = tn = 0
    for expected, observed in zip(truth, prediction, strict=True):
        if expected and observed:
            tp += 1
        elif not expected and observed:
            fp += 1
        elif expected and not observed:
            fn += 1
        else:
            tn += 1
    return ConfusionMatrix(tp=tp, fp=fp, fn=fn, tn=tn)


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else math.nan


def performance(cm: ConfusionMatrix) -> dict[str, float]:
    sensitivity = safe_divide(cm.tp, cm.tp + cm.fn)
    specificity = safe_divide(cm.tn, cm.tn + cm.fp)
    ppv = safe_divide(cm.tp, cm.tp + cm.fp)
    npv = safe_divide(cm.tn, cm.tn + cm.fn)
    f1 = safe_divide(2 * ppv * sensitivity, ppv + sensitivity)
    return {
        "Sensitivity_pct": 100 * sensitivity,
        "Specificity_pct": 100 * specificity,
        "PPV_pct": 100 * ppv,
        "NPV_pct": 100 * npv,
        "F1": f1,
    }


def cohen_kappa_from_cm(cm: ConfusionMatrix) -> float:
    """Cohen's kappa calculated directly from a binary confusion matrix."""

    if not cm.n:
        return math.nan
    observed = (cm.tp + cm.tn) / cm.n
    expected = (
        (cm.tp + cm.fp) * (cm.tp + cm.fn)
        + (cm.fn + cm.tn) * (cm.fp + cm.tn)
    ) / (cm.n * cm.n)
    return safe_divide(observed - expected, 1 - expected)


def fleiss_kappa_binary(raters: Sequence[Sequence[bool]]) -> float:
    """Fleiss' kappa for two-category decisions from two or more raters."""

    if len(raters) < 2:
        raise ValueError("Fleiss' kappa requires at least two raters")
    lengths = {len(rater) for rater in raters}
    if len(lengths) != 1:
        raise ValueError("All raters must have the same number of decisions")
    n = lengths.pop()
    if not n:
        return math.nan

    number_of_raters = len(raters)
    positive_total = sum(sum(int(value) for value in rater) for rater in raters)
    positive_prevalence = positive_total / (n * number_of_raters)
    negative_prevalence = 1 - positive_prevalence
    expected = positive_prevalence**2 + negative_prevalence**2

    agreement_sum = 0.0
    for item in zip(*raters, strict=True):
        positive = sum(int(value) for value in item)
        negative = number_of_raters - positive
        agreement_sum += (
            positive**2 + negative**2 - number_of_raters
        ) / (number_of_raters * (number_of_raters - 1))
    observed = agreement_sum / n
    return safe_divide(observed - expected, 1 - expected)

