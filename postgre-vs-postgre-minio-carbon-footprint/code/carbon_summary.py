from __future__ import annotations

import csv
from pathlib import Path

from carbon_utils import POSTGRES_MINIO_PHASE, POSTGRES_PHASE, build_comparison_breakdown, code_dir, load_phase_totals
from reporting_utils import safe_float


def _format_float(value: float | None, digits: int = 6) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def _pct_change(current: float | None, baseline: float | None) -> str:
    if current is None or baseline in (None, 0.0):
        return "N/A"
    return f"{((current - baseline) / baseline) * 100:+.2f}%"


def _write_breakdown_csv(path: Path, rows: list[dict[str, float | str]]) -> None:
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base_dir = code_dir()
    phase_totals = load_phase_totals(base_dir)
    pg_phase = phase_totals.get(POSTGRES_PHASE)
    pm_phase = phase_totals.get(POSTGRES_MINIO_PHASE)

    if not pg_phase or not pm_phase:
        print("No emissions data found. Run run_all.sh first.")
        return

    results_dir = base_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    breakdown_rows = build_comparison_breakdown(base_dir)
    breakdown_csv_path = results_dir / "carbon_profile_breakdown.csv"
    _write_breakdown_csv(breakdown_csv_path, breakdown_rows)

    metrics = [
        ("Duration (s)", "duration"),
        ("Energy Consumed (kWh)", "energy_consumed"),
        ("CPU Energy (kWh)", "cpu_energy"),
        ("GPU Energy (kWh)", "gpu_energy"),
        ("RAM Energy (kWh)", "ram_energy"),
        ("Emissions (kg CO2 eq)", "emissions"),
        ("Emissions Rate (kg CO2 eq / s)", "emissions_rate"),
    ]

    md_lines = [
        "# Carbon Footprint Measurement Results",
        "",
        "This report compares the energy consumption and CO2 emissions of PostgreSQL+MinIO and PostgreSQL benchmark phases.",
        "",
        "| Metric | PostgreSQL+MinIO Phase | PostgreSQL Phase |",
        "| --- | --- | --- |",
    ]

    for label, key in metrics:
        pm_value = safe_float(pm_phase, key)
        pg_value = safe_float(pg_phase, key)
        md_lines.append(
            f"| {label} | {_format_float(pm_value)} | {_format_float(pg_value)} |"
        )

    pm_energy = safe_float(pm_phase, "energy_consumed")
    pg_energy = safe_float(pg_phase, "energy_consumed")
    pm_emissions = safe_float(pm_phase, "emissions")
    pg_emissions = safe_float(pg_phase, "emissions")

    md_lines.extend(
        [
            "",
            "## Summary Information",
            f"- **PostgreSQL+MinIO Energy compared to PostgreSQL**: {_pct_change(pm_energy, pg_energy)}",
            f"- **PostgreSQL+MinIO Emissions compared to PostgreSQL**: {_pct_change(pm_emissions, pg_emissions)}",
        ]
    )

    if breakdown_rows:
        md_lines.extend(
            [
                "",
                "## Estimated Per-Profile Breakdown",
                "",
                "| Profile | PG Duration (s) | PM Duration (s) | PG Emissions (mg) | PM Emissions (mg) |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in breakdown_rows:
            md_lines.append(
                "| "
                f"{row['profile_label']} | "
                f"{_format_float(float(row['pg_duration_sec']), 1)} | "
                f"{_format_float(float(row['pm_duration_sec']), 1)} | "
                f"{_format_float(float(row['pg_emissions_mg']), 1)} | "
                f"{_format_float(float(row['pm_emissions_mg']), 1)} |"
            )

    markdown_path = results_dir / "carbon_results.md"
    markdown_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote carbon markdown summary to {markdown_path}")
    if breakdown_rows:
        print(f"Wrote per-profile carbon breakdown to {breakdown_csv_path}")


if __name__ == "__main__":
    main()
