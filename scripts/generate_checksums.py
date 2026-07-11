"""Regenerate SHA-256 checksums for the frozen public research artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def selected_files() -> list[Path]:
    patterns = (
        "data/locked/*.csv",
        "data/codebook.csv",
        "results/published/*.csv",
        "prompts/**/*.md",
        "provenance/reconciliation_decisions.csv",
        "provenance/run_manifest.csv",
    )
    files: set[Path] = set()
    for pattern in patterns:
        files.update(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> None:
    lines = []
    for path in selected_files():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(ROOT).as_posix()
        lines.append(f"{digest}  {relative}")
    destination = ROOT / "provenance" / "checksums.sha256"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} checksums to {destination}")


if __name__ == "__main__":
    main()
