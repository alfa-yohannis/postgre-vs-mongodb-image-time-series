from __future__ import annotations

import csv
import shutil
from pathlib import Path


def append_row(path: Path, fieldnames: list[str], row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def load_column(path: Path, column_name: str) -> list[float]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return [float(row[column_name]) for row in reader]


def load_last_value(path: Path, column_name: str) -> float:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"No rows found in {path}")
    return float(rows[-1][column_name])


def load_last_text(path: Path, column_name: str) -> str:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"No rows found in {path}")
    return rows[-1][column_name]


def bytes_to_mb(value: int | float) -> float:
    return float(value) / (1024 * 1024)


def copy_if_present(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
