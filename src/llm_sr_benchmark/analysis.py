"""Locked endpoint definitions and publication-table generation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable

from .metrics import (
    cohen_kappa_from_cm,
    confusion_matrix,
    fleiss_kappa_binary,
    performance,
)


@dataclass(frozen=True)
class EndpointSpec:
    review: str
    data_file: str
    model: str
    endpoint: str
    truth: str
    chatgpt: str
    gemini: str
    gate: str | None = None
    chatgpt_missing: str | None = None
    gemini_missing: str | None = None


ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec(
        "SR1", "sr1.csv", "Model 1 (TF)", "Title screening",
        "human_title", "chatgpt_title", "gemini_title",
        chatgpt_missing="chatgpt_title_missing",
        gemini_missing="gemini_title_missing",
    ),
    EndpointSpec(
        "SR1", "sr1.csv", "Model 1 (TF)", "Title/abstract screening",
        "human_title_abstract", "chatgpt_title_abstract", "gemini_title_abstract",
        gate="human_title",
        chatgpt_missing="chatgpt_title_abstract_missing",
        gemini_missing="gemini_title_abstract_missing",
    ),
    EndpointSpec(
        "SR1", "sr1.csv", "Model 1 (TF)", "Full-text inclusion",
        "human_final", "chatgpt_full_text_tf", "gemini_full_text_tf",
        gate="human_title_abstract",
        chatgpt_missing="chatgpt_full_text_tf_missing",
        gemini_missing="gemini_full_text_tf_missing",
    ),
    EndpointSpec(
        "SR1", "sr1.csv", "Model 2 (nTF)", "Final inclusion",
        "human_final", "chatgpt_final_ntf", "gemini_final_ntf",
        chatgpt_missing="chatgpt_final_missing",
        gemini_missing="gemini_final_missing",
    ),
    EndpointSpec(
        "SR1", "sr1.csv", "One-shot (exploratory)", "Full-text inclusion",
        "human_final", "chatgpt_one_shot", "gemini_one_shot",
        chatgpt_missing="chatgpt_one_shot_missing",
        gemini_missing="gemini_one_shot_missing",
    ),
    EndpointSpec(
        "SR2", "sr2.csv", "Model 2 (nTF)", "Final inclusion",
        "human_final", "chatgpt_final_ntf", "gemini_final_ntf",
        chatgpt_missing="chatgpt_final_missing",
        gemini_missing="gemini_final_missing",
    ),
    EndpointSpec(
        "SR3", "sr3.csv", "Model 1 (TF)", "Title/abstract screening",
        "human_title_abstract", "chatgpt_title_abstract", "gemini_title_abstract",
        chatgpt_missing="chatgpt_title_abstract_missing",
        gemini_missing="gemini_title_abstract_missing",
    ),
    EndpointSpec(
        "SR3", "sr3.csv", "Model 1 (TF)", "Full-text inclusion",
        "human_final", "chatgpt_full_text_tf", "gemini_full_text_tf",
        gate="human_title_abstract",
        chatgpt_missing="chatgpt_full_text_tf_missing",
        gemini_missing="gemini_full_text_tf_missing",
    ),
    EndpointSpec(
        "SR3", "sr3.csv", "Model 2 (nTF)", "Final inclusion",
        "human_final", "chatgpt_final_ntf", "gemini_final_ntf",
        chatgpt_missing="chatgpt_final_missing",
        gemini_missing="gemini_final_missing",
    ),
)


TABLE1_COLUMNS = (
    "Review", "Model", "Endpoint", "LLM", "N", "TP", "FP", "FN", "TN",
    "Sensitivity_pct", "Specificity_pct", "PPV_pct", "NPV_pct", "F1",
    "Cohen_kappa", "Model_missing_outputs",
)

TABLE2_COLUMNS = (
    "Review", "Model", "Endpoint", "N",
    "Human_vs_ChatGPT_Cohen_kappa", "Human_vs_Gemini_Cohen_kappa",
    "ChatGPT_vs_Gemini_Cohen_kappa", "Human_ChatGPT_Gemini_Fleiss_kappa",
)

HETEROGENEITY_COLUMNS = (
    "Model", "Measure", "Q", "df", "p_value", "I2_pct",
    "inverse_variance_mean", "SR1", "SR2", "SR3",
)


def bit(row: dict[str, str], field: str) -> bool:
    return row[field] == "1"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    # Derived end-to-end decisions are intentionally calculated here rather
    # than duplicated in the public data files. This makes the staged logic
    # explicit and prevents a stale derived column from drifting out of sync.
    if path.name == "sr1.csv":
        for row in rows:
            row["chatgpt_final_ntf"] = str(int(
                bit(row, "chatgpt_title")
                and bit(row, "chatgpt_title_abstract")
                and bit(row, "chatgpt_one_shot")
            ))
            row["gemini_final_ntf"] = str(int(
                bit(row, "gemini_title")
                and bit(row, "gemini_title_abstract")
                and bit(row, "gemini_one_shot")
            ))
            row["chatgpt_final_missing"] = str(int(
                bit(row, "chatgpt_title")
                and bit(row, "chatgpt_title_abstract")
                and bit(row, "chatgpt_one_shot_missing")
            ))
            row["gemini_final_missing"] = str(int(
                bit(row, "gemini_title")
                and bit(row, "gemini_title_abstract")
                and bit(row, "gemini_one_shot_missing")
            ))
    elif path.name == "sr2.csv":
        for row in rows:
            row["chatgpt_final_ntf"] = str(int(
                bit(row, "chatgpt_title_abstract")
                and bit(row, "chatgpt_full_text_ntf")
            ))
            row["gemini_final_ntf"] = str(int(
                bit(row, "gemini_title_abstract")
                and bit(row, "gemini_full_text_ntf")
            ))
            row["chatgpt_final_missing"] = str(int(
                bit(row, "chatgpt_title_abstract")
                and bit(row, "chatgpt_full_text_ntf_missing")
            ))
            row["gemini_final_missing"] = str(int(
                bit(row, "gemini_title_abstract")
                and bit(row, "gemini_full_text_ntf_missing")
            ))
    elif path.name == "sr3.csv":
        for row in rows:
            row["chatgpt_final_ntf"] = str(int(
                bit(row, "chatgpt_title_abstract")
                and bit(row, "chatgpt_full_text_tf")
            ))
            row["gemini_final_ntf"] = str(int(
                bit(row, "gemini_title_abstract")
                and bit(row, "gemini_full_text_tf")
            ))
            row["chatgpt_final_missing"] = str(int(
                bit(row, "chatgpt_title_abstract")
                and bit(row, "chatgpt_full_text_tf_missing")
            ))
            row["gemini_final_missing"] = str(int(
                bit(row, "gemini_title_abstract")
                and bit(row, "gemini_full_text_tf_missing")
            ))
    return rows


def select(rows: Iterable[dict[str, str]], gate: str | None) -> list[dict[str, str]]:
    if gate is None:
        return list(rows)
    return [row for row in rows if bit(row, gate)]


def build_tables(data_dir: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    cache: dict[str, list[dict[str, str]]] = {}
    table1: list[dict[str, object]] = []
    table2: list[dict[str, object]] = []

    for spec in ENDPOINTS:
        rows = cache.setdefault(spec.data_file, load_rows(data_dir / spec.data_file))
        subset = select(rows, spec.gate)
        truth = [bit(row, spec.truth) for row in subset]
        predictions = {
            "ChatGPT": [bit(row, spec.chatgpt) for row in subset],
            "Gemini": [bit(row, spec.gemini) for row in subset],
        }

        kappas: dict[str, float] = {}
        for model_name, prediction in predictions.items():
            field = spec.chatgpt if model_name == "ChatGPT" else spec.gemini
            missing_field = (
                spec.chatgpt_missing if model_name == "ChatGPT" else spec.gemini_missing
            )
            cm = confusion_matrix(truth, prediction)
            kappa = cohen_kappa_from_cm(cm)
            kappas[model_name] = kappa
            row: dict[str, object] = {
                "Review": spec.review,
                "Model": spec.model,
                "Endpoint": spec.endpoint,
                "LLM": model_name,
                "N": cm.n,
                **cm.as_dict(),
                **performance(cm),
                "Cohen_kappa": kappa,
                "Model_missing_outputs": (
                    sum(bit(item, missing_field) for item in subset) if missing_field else 0
                ),
            }
            # Retain a local name for easier debugging without exposing it in CSV output.
            _ = field
            table1.append(row)

        chatgpt_gemini_cm = confusion_matrix(
            predictions["ChatGPT"], predictions["Gemini"]
        )
        table2.append({
            "Review": spec.review,
            "Model": spec.model,
            "Endpoint": spec.endpoint,
            "N": len(subset),
            "Human_vs_ChatGPT_Cohen_kappa": kappas["ChatGPT"],
            "Human_vs_Gemini_Cohen_kappa": kappas["Gemini"],
            "ChatGPT_vs_Gemini_Cohen_kappa": cohen_kappa_from_cm(chatgpt_gemini_cm),
            "Human_ChatGPT_Gemini_Fleiss_kappa": fleiss_kappa_binary(
                [truth, predictions["ChatGPT"], predictions["Gemini"]]
            ),
        })
    return table1, table2


def cochran_q_proportions(
    success_total_pairs: list[tuple[int, int]],
) -> tuple[float, int, float, float, float]:
    proportions = [success / total for success, total in success_total_pairs]
    weights = [
        1 / (proportion * (1 - proportion) / total)
        for proportion, (_, total) in zip(
            proportions, success_total_pairs, strict=True
        )
    ]
    mean = sum(weight * value for weight, value in zip(weights, proportions, strict=True)) / sum(weights)
    q = sum(
        weight * (value - mean) ** 2
        for weight, value in zip(weights, proportions, strict=True)
    )
    degrees_of_freedom = len(proportions) - 1
    if degrees_of_freedom != 2:
        raise ValueError("The locked heterogeneity analysis requires exactly three reviews")
    p_value = math.exp(-q / 2)
    i2 = max(0.0, (q - degrees_of_freedom) / q) * 100 if q else 0.0
    return q, degrees_of_freedom, p_value, i2, mean


def build_heterogeneity(table1: list[dict[str, object]]) -> list[dict[str, object]]:
    final_rows = {
        (str(row["Review"]), str(row["LLM"])): row
        for row in table1
        if row["Model"] == "Model 2 (nTF)" and row["Endpoint"] == "Final inclusion"
    }
    output: list[dict[str, object]] = []
    for model in ("ChatGPT", "Gemini"):
        review_rows = [final_rows[(review, model)] for review in ("SR1", "SR2", "SR3")]
        for measure, success, other in (
            ("Sensitivity", "TP", "FN"),
            ("Specificity", "TN", "FP"),
        ):
            pairs = [
                (int(row[success]), int(row[success]) + int(row[other]))
                for row in review_rows
            ]
            q, df, p_value, i2, mean = cochran_q_proportions(pairs)
            output.append({
                "Model": model,
                "Measure": measure,
                "Q": q,
                "df": df,
                "p_value": p_value,
                "I2_pct": i2,
                "inverse_variance_mean": mean,
                "SR1": pairs[0][0] / pairs[0][1],
                "SR2": pairs[1][0] / pairs[1][1],
                "SR3": pairs[2][0] / pairs[2][1],
            })
    return output


def write_csv(path: Path, rows: list[dict[str, object]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def reproduce(data_dir: Path, output_dir: Path) -> None:
    table1, table2 = build_tables(data_dir)
    heterogeneity = build_heterogeneity(table1)
    write_csv(output_dir / "table1_validity.csv", table1, TABLE1_COLUMNS)
    write_csv(output_dir / "table2_agreement.csv", table2, TABLE2_COLUMNS)
    write_csv(output_dir / "heterogeneity.csv", heterogeneity, HETEROGENEITY_COLUMNS)
