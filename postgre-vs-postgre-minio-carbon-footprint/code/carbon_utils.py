from __future__ import annotations

from pathlib import Path

from reporting_utils import PROFILE_ORDER, load_last_rows_by_profile, profile_label, resolve_result_path, safe_float


POSTGRES_PHASE = "postgres_phase"
POSTGRES_MINIO_PHASE = "postgres_minio_phase"

POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary"
POSTGRES_MINIO_INSERT_SUMMARY = "results_postgres_minio_insert_summary"
POSTGRES_RETRIEVE_SUMMARY = "results_postgres_retrieve_summary"
POSTGRES_MINIO_RETRIEVE_SUMMARY = "results_postgres_minio_retrieve_summary"
POSTGRES_POINT_READ_SUMMARY = "results_postgres_point_read_summary"
POSTGRES_MINIO_POINT_READ_SUMMARY = "results_postgres_minio_point_read_summary"


def code_dir() -> Path:
    return Path(__file__).resolve().parent


def load_phase_totals(base_dir: Path) -> dict[str, dict[str, str]]:
    emissions_path = resolve_result_path(base_dir, "emissions.csv")
    if not emissions_path.exists():
        return {}

    rows: list[dict[str, str]] = []
    import csv

    with emissions_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    return {
        row["project_name"]: row
        for row in rows
        if row.get("project_name")
    }


def _load_rows_by_profile_with_fallback(
    base_dir: Path,
    *stems: str,
) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for stem in stems:
        for profile, row in load_last_rows_by_profile(base_dir, stem).items():
            merged.setdefault(profile, row)
    return merged


def _mean_run_seconds(
    row: dict[str, str] | None,
    mean_column: str,
    runs_column: str,
    *,
    scale: float = 1.0,
) -> float:
    mean_value = safe_float(row, mean_column)
    runs_value = safe_float(row, runs_column)
    if mean_value is None or runs_value is None:
        return 0.0
    return mean_value * runs_value * scale


def _phase_rates(phase_row: dict[str, str]) -> dict[str, float] | None:
    duration_sec = safe_float(phase_row, "duration")
    if duration_sec is None or duration_sec <= 0.0:
        return None

    return {
        "duration_sec": duration_sec,
        "energy_rate_kwh_per_sec": (safe_float(phase_row, "energy_consumed") or 0.0) / duration_sec,
        "cpu_rate_kwh_per_sec": (safe_float(phase_row, "cpu_energy") or 0.0) / duration_sec,
        "ram_rate_kwh_per_sec": (safe_float(phase_row, "ram_energy") or 0.0) / duration_sec,
        "emissions_rate_kg_per_sec": (safe_float(phase_row, "emissions") or 0.0) / duration_sec,
    }


def build_phase_profile_breakdown(
    base_dir: Path,
    phase_name: str,
    *,
    insert_stem: str,
    retrieval_stems: tuple[str, ...],
) -> list[dict[str, float | str]]:
    phase_rows = load_phase_totals(base_dir)
    phase_row = phase_rows.get(phase_name)
    if not phase_row:
        return []

    rates = _phase_rates(phase_row)
    if not rates:
        return []

    insert_rows = load_last_rows_by_profile(base_dir, insert_stem)
    retrieval_rows = _load_rows_by_profile_with_fallback(base_dir, *retrieval_stems)

    rows: list[dict[str, float | str]] = []
    for profile in PROFILE_ORDER:
        insert_row = insert_rows.get(profile)
        retrieval_row = retrieval_rows.get(profile)

        insert_duration_sec = _mean_run_seconds(
            insert_row,
            "mean_duration_sec",
            "n_runs",
        )
        retrieval_duration_sec = _mean_run_seconds(
            retrieval_row,
            "mean_latency_ms",
            "n_runs",
            scale=1.0 / 1000.0,
        )
        total_duration_sec = insert_duration_sec + retrieval_duration_sec

        if total_duration_sec <= 0.0:
            continue

        insert_emissions_mg = rates["emissions_rate_kg_per_sec"] * insert_duration_sec * 1_000_000
        retrieval_emissions_mg = (
            rates["emissions_rate_kg_per_sec"] * retrieval_duration_sec * 1_000_000
        )

        rows.append(
            {
                "profile": profile,
                "profile_label": profile_label(profile),
                "phase_name": phase_name,
                "insert_duration_sec": insert_duration_sec,
                "retrieval_duration_sec": retrieval_duration_sec,
                "point_read_duration_sec": retrieval_duration_sec,
                "duration_sec": total_duration_sec,
                "energy_uwh": rates["energy_rate_kwh_per_sec"] * total_duration_sec * 1_000_000,
                "cpu_uwh": rates["cpu_rate_kwh_per_sec"] * total_duration_sec * 1_000_000,
                "ram_uwh": rates["ram_rate_kwh_per_sec"] * total_duration_sec * 1_000_000,
                "insert_emissions_mg": insert_emissions_mg,
                "retrieval_emissions_mg": retrieval_emissions_mg,
                "point_read_emissions_mg": retrieval_emissions_mg,
                "emissions_mg": insert_emissions_mg + retrieval_emissions_mg,
            }
        )

    return rows


def build_comparison_breakdown(base_dir: Path) -> list[dict[str, float | str]]:
    pg_rows = {
        row["profile"]: row
        for row in build_phase_profile_breakdown(
            base_dir,
            POSTGRES_PHASE,
            insert_stem=POSTGRES_INSERT_SUMMARY,
            retrieval_stems=(POSTGRES_RETRIEVE_SUMMARY, POSTGRES_POINT_READ_SUMMARY),
        )
    }
    pm_rows = {
        row["profile"]: row
        for row in build_phase_profile_breakdown(
            base_dir,
            POSTGRES_MINIO_PHASE,
            insert_stem=POSTGRES_MINIO_INSERT_SUMMARY,
            retrieval_stems=(
                POSTGRES_MINIO_RETRIEVE_SUMMARY,
                POSTGRES_MINIO_POINT_READ_SUMMARY,
            ),
        )
    }

    rows: list[dict[str, float | str]] = []
    for profile in PROFILE_ORDER:
        pg_row = pg_rows.get(profile)
        pm_row = pm_rows.get(profile)
        if not pg_row and not pm_row:
            continue

        rows.append(
            {
                "profile": profile,
                "profile_label": profile_label(profile),
                "pg_insert_duration_sec": (pg_row or {}).get("insert_duration_sec", 0.0),
                "pg_retrieval_duration_sec": (pg_row or {}).get("retrieval_duration_sec", 0.0),
                "pg_point_read_duration_sec": (pg_row or {}).get("point_read_duration_sec", 0.0),
                "pg_duration_sec": (pg_row or {}).get("duration_sec", 0.0),
                "pg_energy_uwh": (pg_row or {}).get("energy_uwh", 0.0),
                "pg_cpu_uwh": (pg_row or {}).get("cpu_uwh", 0.0),
                "pg_ram_uwh": (pg_row or {}).get("ram_uwh", 0.0),
                "pg_insert_emissions_mg": (pg_row or {}).get("insert_emissions_mg", 0.0),
                "pg_retrieval_emissions_mg": (pg_row or {}).get("retrieval_emissions_mg", 0.0),
                "pg_point_read_emissions_mg": (pg_row or {}).get("point_read_emissions_mg", 0.0),
                "pg_emissions_mg": (pg_row or {}).get("emissions_mg", 0.0),
                "pm_insert_duration_sec": (pm_row or {}).get("insert_duration_sec", 0.0),
                "pm_retrieval_duration_sec": (pm_row or {}).get("retrieval_duration_sec", 0.0),
                "pm_point_read_duration_sec": (pm_row or {}).get("point_read_duration_sec", 0.0),
                "pm_duration_sec": (pm_row or {}).get("duration_sec", 0.0),
                "pm_energy_uwh": (pm_row or {}).get("energy_uwh", 0.0),
                "pm_cpu_uwh": (pm_row or {}).get("cpu_uwh", 0.0),
                "pm_ram_uwh": (pm_row or {}).get("ram_uwh", 0.0),
                "pm_insert_emissions_mg": (pm_row or {}).get("insert_emissions_mg", 0.0),
                "pm_retrieval_emissions_mg": (pm_row or {}).get("retrieval_emissions_mg", 0.0),
                "pm_point_read_emissions_mg": (pm_row or {}).get("point_read_emissions_mg", 0.0),
                "pm_emissions_mg": (pm_row or {}).get("emissions_mg", 0.0),
            }
        )

    return rows
