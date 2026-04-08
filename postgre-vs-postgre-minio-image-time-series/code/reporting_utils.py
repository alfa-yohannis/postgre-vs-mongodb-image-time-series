from __future__ import annotations

import csv
from pathlib import Path


PROFILE_ORDER = [
    "360p_sd_image",
    "480p_sd_image",
    "720p_hd_image",
    "1080p_fhd_image",
    "1440p_qhd_image",
    "4k_uhd_image",
    "5k_uhd_image",
]

PROFILE_TO_LABEL = {
    "360p_sd_image": "360p",
    "480p_sd_image": "480p",
    "720p_hd_image": "720p",
    "1080p_fhd_image": "1080p",
    "1440p_qhd_image": "1440p",
    "4k_uhd_image": "4K",
    "5k_uhd_image": "5K",
}


def profile_label(profile: str) -> str:
    return PROFILE_TO_LABEL.get(profile, profile)


def candidate_result_dirs(base_dir: Path) -> list[Path]:
    return [base_dir / "results", base_dir]


def resolve_result_path(base_dir: Path, filename: str) -> Path:
    for directory in candidate_result_dirs(base_dir):
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return candidate_result_dirs(base_dir)[0] / filename


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def load_last_row(path: Path) -> dict[str, str] | None:
    rows = load_csv_rows(path)
    return rows[-1] if rows else None


def load_last_rows_by_profile(base_dir: Path, stem: str) -> dict[str, dict[str, str]]:
    data: dict[str, dict[str, str]] = {}
    for profile in PROFILE_ORDER:
        row = load_last_row(resolve_result_path(base_dir, f"{stem}_{profile}.csv"))
        if row:
            data[profile] = row
    return data


def load_driver_rows(base_dir: Path, filename: str) -> dict[str, dict[str, str]]:
    rows = load_csv_rows(resolve_result_path(base_dir, filename))
    if not rows:
        return {}

    by_profile = {
        row["profile"]: row
        for row in rows
        if row.get("profile")
    }
    if by_profile:
        return {profile: by_profile[profile] for profile in PROFILE_ORDER if profile in by_profile}

    tail = rows[-len(PROFILE_ORDER) :]
    return {
        profile: row
        for profile, row in zip(PROFILE_ORDER, tail, strict=False)
    }


def safe_float(row: dict[str, str] | None, column: str) -> float | None:
    if not row:
        return None
    raw = row.get(column)
    if raw in (None, ""):
        return None
    return float(raw)
