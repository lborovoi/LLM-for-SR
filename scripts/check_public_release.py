"""Fail if the public repository contains common private-release hazards."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {
    ".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ris", ".nbib", ".ipynb",
    ".pyc", ".pkl", ".pickle",
}
TEXT_SUFFIXES = {
    "", ".cff", ".csv", ".gitignore", ".gitattributes", ".md", ".py",
    ".sha256", ".toml", ".txt", ".yaml", ".yml",
}
SUSPICIOUS_PATTERNS = {
    "absolute user path": re.compile(r"[A-Za-z]:\\\\Users\\\\", re.IGNORECASE),
    "API-key-like token": re.compile(r"\bsk-(?:or-)?[A-Za-z0-9_-]{20,}\b"),
    "private-key block": re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "unprofessional scratch label": re.compile(
        r"\b(?:fuc" + r"king|stu" + r"pid_merge)\b", re.IGNORECASE
    ),
}
ALLOWED_DATA_FIELDS = {
    "record_id",
    "human_title", "human_title_abstract", "human_final",
    "chatgpt_title", "gemini_title",
    "chatgpt_title_abstract", "gemini_title_abstract",
    "chatgpt_full_text_tf", "gemini_full_text_tf",
    "chatgpt_full_text_ntf", "gemini_full_text_ntf",
    "chatgpt_one_shot", "gemini_one_shot",
    "chatgpt_title_missing", "gemini_title_missing",
    "chatgpt_title_abstract_missing", "gemini_title_abstract_missing",
    "chatgpt_full_text_tf_missing", "gemini_full_text_tf_missing",
    "chatgpt_full_text_ntf_missing", "gemini_full_text_ntf_missing",
    "chatgpt_one_shot_missing", "gemini_one_shot_missing",
}


def relative_files() -> list[Path]:
    ignored_parts = {".git", "__pycache__", ".pytest_cache"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not ignored_parts.intersection(path.parts)
        and not any(part.endswith(".egg-info") for part in path.parts)
    ]


def check_files() -> list[str]:
    errors: list[str] = []
    for path in relative_files():
        relative = path.relative_to(ROOT)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden file type: {relative}")
        if path.stat().st_size > 5_000_000:
            errors.append(f"unexpectedly large file: {relative}")
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE"}:
            errors.append(f"unreviewed file type: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            errors.append(f"non-UTF-8 text file: {relative}")
            continue
        for label, pattern in SUSPICIOUS_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label}: {relative}")
    return errors


def check_data() -> list[str]:
    errors: list[str] = []
    for path in sorted((ROOT / "data" / "locked").glob("sr*.csv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            unexpected = fields - ALLOWED_DATA_FIELDS
            if unexpected:
                errors.append(f"unexpected data fields in {path.name}: {sorted(unexpected)}")
            for row_number, row in enumerate(reader, start=2):
                identifier = row.get("record_id", "")
                if not re.fullmatch(r"SR[123]-[0-9a-f]{16}", identifier):
                    errors.append(f"invalid opaque ID in {path.name}:{row_number}")
                    break
                values = [value for field, value in row.items() if field != "record_id"]
                if any(value not in {"0", "1"} for value in values):
                    errors.append(f"non-binary public decision in {path.name}:{row_number}")
                    break
    return errors


def check_checksums() -> list[str]:
    manifest = ROOT / "provenance" / "checksums.sha256"
    if not manifest.exists():
        return ["missing provenance/checksums.sha256"]
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", maxsplit=1)
        path = ROOT / relative
        if not path.exists():
            errors.append(f"checksum target missing: {relative}")
            continue
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != expected:
            errors.append(f"checksum mismatch: {relative}")
    return errors


def main() -> int:
    errors = check_files() + check_data() + check_checksums()
    if errors:
        print("Public-release check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Public-release check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
