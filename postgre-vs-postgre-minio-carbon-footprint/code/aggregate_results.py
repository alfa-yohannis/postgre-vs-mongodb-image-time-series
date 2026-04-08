from __future__ import annotations

from pathlib import Path

from reporting_utils import (
    PROFILE_ORDER,
    load_last_rows_by_profile,
    profile_label,
    safe_float,
)


POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary"
POSTGRES_MINIO_INSERT_SUMMARY = "results_postgres_minio_insert_summary"
POSTGRES_POINT_READ_SUMMARY = "results_postgres_point_read_summary"
POSTGRES_MINIO_POINT_READ_SUMMARY = "results_postgres_minio_point_read_summary"


def code_dir() -> Path:
    return Path(__file__).resolve().parent


def write_text_summary() -> Path:
    pg_insert = load_last_rows_by_profile(code_dir(), POSTGRES_INSERT_SUMMARY)
    pm_insert = load_last_rows_by_profile(code_dir(), POSTGRES_MINIO_INSERT_SUMMARY)
    pg_read = load_last_rows_by_profile(code_dir(), POSTGRES_POINT_READ_SUMMARY)
    pm_read = load_last_rows_by_profile(code_dir(), POSTGRES_MINIO_POINT_READ_SUMMARY)

    lines = ["PG vs PM benchmark summary", ""]
    for profile in PROFILE_ORDER:
        pg_insert_row = pg_insert.get(profile)
        pm_insert_row = pm_insert.get(profile)
        pg_read_row = pg_read.get(profile)
        pm_read_row = pm_read.get(profile)
        if not any((pg_insert_row, pm_insert_row, pg_read_row, pm_read_row)):
            continue

        lines.append(f"Profile: {profile_label(profile)}")
        if pg_insert_row:
            lines.append(
                "  PG insert: "
                f"{safe_float(pg_insert_row, 'mean_rows_per_sec'):.2f} rows/s | "
                f"amp={safe_float(pg_insert_row, 'mean_storage_amplification'):.4f} | "
                f"disk={safe_float(pg_insert_row, 'mean_table_total_after_mb'):.3f} MB"
            )
        if pm_insert_row:
            lines.append(
                "  PM insert: "
                f"{safe_float(pm_insert_row, 'mean_rows_per_sec'):.2f} rows/s | "
                f"amp={safe_float(pm_insert_row, 'mean_storage_amplification'):.4f} | "
                f"disk={safe_float(pm_insert_row, 'mean_table_total_after_mb'):.3f} MB"
            )
        if pg_read_row:
            lines.append(
                f"  PG point read: {safe_float(pg_read_row, 'mean_latency_ms'):.3f} ms"
            )
        if pm_read_row:
            lines.append(
                f"  PM point read: {safe_float(pm_read_row, 'mean_latency_ms'):.3f} ms"
            )
        lines.append("")

    output_path = code_dir() / "all_summaries.txt"
    output_path.write_text("\n".join(lines))
    return output_path


def main() -> None:
    summary_path = write_text_summary()
    print(f"Wrote aggregated text summary to {summary_path.name}")


if __name__ == "__main__":
    main()
