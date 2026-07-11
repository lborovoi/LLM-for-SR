"""Structural and logical validation for the public locked datasets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetExpectation:
    filename: str
    records: int
    positive_counts: dict[str, int]


EXPECTATIONS = {
    "SR1": DatasetExpectation(
        filename="sr1.csv",
        records=1556,
        positive_counts={
            "human_title": 496,
            "human_title_abstract": 86,
            "human_final": 28,
        },
    ),
    "SR2": DatasetExpectation(
        filename="sr2.csv",
        records=3720,
        positive_counts={"human_final": 74},
    ),
    "SR3": DatasetExpectation(
        filename="sr3.csv",
        records=746,
        positive_counts={
            "human_title_abstract": 101,
            "human_final": 60,
        },
    ),
}


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _bit(row: dict[str, str], field: str) -> int:
    return int(row[field])


def validate_dataset(review: str, data_dir: Path) -> tuple[list[str], str]:
    expectation = EXPECTATIONS[review]
    fields, rows = load(data_dir / expectation.filename)
    errors: list[str] = []

    if len(rows) != expectation.records:
        errors.append(
            f"{review}: expected {expectation.records} rows, found {len(rows)}"
        )
    if not fields or fields[0] != "record_id":
        errors.append(f"{review}: first column must be record_id")

    identifiers = [row.get("record_id", "") for row in rows]
    if any(not value for value in identifiers):
        errors.append(f"{review}: blank record_id")
    if len(set(identifiers)) != len(identifiers):
        errors.append(f"{review}: duplicate record_id")

    binary_fields = [field for field in fields if field != "record_id"]
    for field in binary_fields:
        invalid = [row_number for row_number, row in enumerate(rows, start=2) if row[field] not in {"0", "1"}]
        if invalid:
            errors.append(
                f"{review}: {field} contains non-binary values at rows {invalid[:5]}"
            )

    for field, expected in expectation.positive_counts.items():
        if field not in fields:
            errors.append(f"{review}: missing required field {field}")
            continue
        observed = sum(_bit(row, field) for row in rows)
        if observed != expected:
            errors.append(
                f"{review}: {field} expected {expected} positives, found {observed}"
            )

    if review == "SR1":
        for row_number, row in enumerate(rows, start=2):
            if _bit(row, "human_title_abstract") > _bit(row, "human_title"):
                errors.append(f"SR1 row {row_number}: human stage order is invalid")
            if _bit(row, "human_final") > _bit(row, "human_title_abstract"):
                errors.append(f"SR1 row {row_number}: human final is outside the full-text gate")
    elif review == "SR3":
        for row_number, row in enumerate(rows, start=2):
            if _bit(row, "human_final") > _bit(row, "human_title_abstract"):
                errors.append(f"SR3 row {row_number}: human final is outside the full-text gate")

    summary = ", ".join(
        [f"records={len(rows)}"]
        + [
            f"{field}={sum(_bit(row, field) for row in rows)}"
            for field in expectation.positive_counts
            if field in fields
        ]
    )
    return errors, f"{review}: {summary}"


def validate_all(data_dir: Path) -> list[str]:
    errors: list[str] = []
    for review in EXPECTATIONS:
        dataset_errors, _ = validate_dataset(review, data_dir)
        errors.extend(dataset_errors)
    return errors
