from __future__ import annotations

from pathlib import Path

from reporting_utils import PROFILE_ORDER, load_last_rows_by_profile, profile_label, safe_float


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    pg = load_last_rows_by_profile(base_dir, "results_postgres_insert_summary")
    pm = load_last_rows_by_profile(base_dir, "results_postgres_minio_insert_summary")

    print("--- DISK USAGE (MB) ---")
    for profile in PROFILE_ORDER:
        pg_row = pg.get(profile)
        pm_row = pm.get(profile)
        if not pg_row and not pm_row:
            continue

        pg_disk = safe_float(pg_row, "mean_table_total_after_mb")
        pm_disk = safe_float(pm_row, "mean_table_total_after_mb")
        print(
            f"{profile_label(profile):>5}: "
            f"PG={(f'{pg_disk:.3f}' if pg_disk is not None else 'n/a')} MB, "
            f"PM={(f'{pm_disk:.3f}' if pm_disk is not None else 'n/a')} MB"
        )


if __name__ == "__main__":
    main()
