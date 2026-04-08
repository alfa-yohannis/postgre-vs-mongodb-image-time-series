from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from benchmark_utils import append_row
from reporting_utils import (
    PROFILE_ORDER,
    load_driver_rows,
    load_last_rows_by_profile,
    profile_label,
    safe_float,
)


POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary"
POSTGRES_MINIO_INSERT_SUMMARY = "results_postgres_minio_insert_summary"
POSTGRES_POINT_READ_SUMMARY = "results_postgres_point_read_summary"
POSTGRES_MINIO_POINT_READ_SUMMARY = "results_postgres_minio_point_read_summary"

FINAL_STATS_CSV = "final_stats_summary.csv"


def code_dir() -> Path:
    return Path(__file__).resolve().parent


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0.0):
        return None
    return numerator / denominator


def build_rows() -> list[dict[str, object]]:
    base_dir = code_dir()
    pg_insert = load_last_rows_by_profile(base_dir, POSTGRES_INSERT_SUMMARY)
    pm_insert = load_last_rows_by_profile(base_dir, POSTGRES_MINIO_INSERT_SUMMARY)
    pg_read = load_last_rows_by_profile(base_dir, POSTGRES_POINT_READ_SUMMARY)
    pm_read = load_last_rows_by_profile(base_dir, POSTGRES_MINIO_POINT_READ_SUMMARY)
    pg_driver = load_driver_rows(base_dir, "results_postgres_driver_summary.csv")
    pm_driver = load_driver_rows(base_dir, "results_minio_driver_summary.csv")

    rows: list[dict[str, object]] = []
    timestamp = datetime.now(timezone.utc).isoformat()

    for profile in PROFILE_ORDER:
        pg_insert_row = pg_insert.get(profile)
        pm_insert_row = pm_insert.get(profile)
        pg_read_row = pg_read.get(profile)
        pm_read_row = pm_read.get(profile)
        if not any((pg_insert_row, pm_insert_row, pg_read_row, pm_read_row)):
            continue

        payload_mb = safe_float(pg_insert_row or pm_insert_row, "payload_size_mb")
        pg_insert_rps = safe_float(pg_insert_row, "mean_rows_per_sec")
        pm_insert_rps = safe_float(pm_insert_row, "mean_rows_per_sec")
        pg_read_ms = safe_float(pg_read_row, "mean_latency_ms")
        pm_read_ms = safe_float(pm_read_row, "mean_latency_ms")
        pg_amp = safe_float(pg_insert_row, "mean_storage_amplification")
        pm_amp = safe_float(pm_insert_row, "mean_storage_amplification")
        pg_disk_mb = safe_float(pg_insert_row, "mean_table_total_after_mb")
        pm_disk_mb = safe_float(pm_insert_row, "mean_table_total_after_mb")
        pg_driver_ms = safe_float(pg_driver.get(profile), "mean_latency_ms")
        minio_driver_ms = safe_float(pm_driver.get(profile), "mean_latency_ms")

        rows.append(
            {
                "timestamp": timestamp,
                "profile": profile,
                "profile_label": profile_label(profile),
                "payload_size_mb": round(payload_mb, 6) if payload_mb is not None else "",
                "pg_insert_rows_per_sec": round(pg_insert_rps, 2) if pg_insert_rps is not None else "",
                "pm_insert_rows_per_sec": round(pm_insert_rps, 2) if pm_insert_rps is not None else "",
                "insert_speedup_pm_vs_pg": round(ratio(pm_insert_rps, pg_insert_rps), 3)
                if ratio(pm_insert_rps, pg_insert_rps) is not None
                else "",
                "pg_point_read_ms": round(pg_read_ms, 3) if pg_read_ms is not None else "",
                "pm_point_read_ms": round(pm_read_ms, 3) if pm_read_ms is not None else "",
                "point_read_speedup_pg_vs_pm": round(ratio(pg_read_ms, pm_read_ms), 3)
                if ratio(pg_read_ms, pm_read_ms) is not None
                else "",
                "pg_storage_amplification": round(pg_amp, 4) if pg_amp is not None else "",
                "pm_storage_amplification": round(pm_amp, 4) if pm_amp is not None else "",
                "pg_disk_mb": round(pg_disk_mb, 3) if pg_disk_mb is not None else "",
                "pm_disk_mb": round(pm_disk_mb, 3) if pm_disk_mb is not None else "",
                "pg_driver_ms": round(pg_driver_ms, 6) if pg_driver_ms is not None else "",
                "minio_driver_ms": round(minio_driver_ms, 6) if minio_driver_ms is not None else "",
            }
        )

    return rows


def print_rows(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("No benchmark summaries found.")
        return

    print("FINAL STATISTICAL SUMMARY")
    for row in rows:
        print(
            f"{row['profile_label']}: "
            f"insert PG={row['pg_insert_rows_per_sec']} rows/s, "
            f"PM={row['pm_insert_rows_per_sec']} rows/s, "
            f"read PG={row['pg_point_read_ms']} ms, "
            f"PM={row['pm_point_read_ms']} ms, "
            f"disk PG={row['pg_disk_mb']} MB, "
            f"PM={row['pm_disk_mb']} MB"
        )


def main() -> None:
    rows = build_rows()
    print_rows(rows)

    output_path = code_dir() / FINAL_STATS_CSV
    if output_path.exists():
        output_path.unlink()

    if not rows:
        return

    fieldnames = list(rows[0].keys())
    for row in rows:
        append_row(output_path, fieldnames, row)

    print(f"Saved final summary to {output_path.name}")


if __name__ == "__main__":
    main()
