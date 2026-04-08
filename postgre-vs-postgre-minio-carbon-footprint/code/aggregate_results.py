from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    "/tmp/postgre-vs-postgre-minio-image-time-series-mplconfig",
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from reporting_utils import (
    PROFILE_ORDER,
    load_csv_rows,
    load_last_rows_by_profile,
    profile_label,
    resolve_result_path,
    safe_float,
)


POSTGRES_INSERT_RUNS = "results_postgres_insert_runs"
POSTGRES_MINIO_INSERT_RUNS = "results_postgres_minio_insert_runs"
POSTGRES_POINT_READ_RUNS = "results_postgres_point_read_runs"
POSTGRES_MINIO_POINT_READ_RUNS = "results_postgres_minio_point_read_runs"

POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary"
POSTGRES_MINIO_INSERT_SUMMARY = "results_postgres_minio_insert_summary"
POSTGRES_POINT_READ_SUMMARY = "results_postgres_point_read_summary"
POSTGRES_MINIO_POINT_READ_SUMMARY = "results_postgres_minio_point_read_summary"


def code_dir() -> Path:
    return Path(__file__).resolve().parent


def figures_dir() -> Path:
    output_dir = code_dir().parent / "paper" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_metric_runs(stem: str, column: str) -> dict[str, list[float]]:
    data: dict[str, list[float]] = {}
    for profile in PROFILE_ORDER:
        rows = load_csv_rows(resolve_result_path(code_dir(), f"{stem}_{profile}.csv"))
        values = [float(row[column]) for row in rows if row.get(column)]
        if values:
            data[profile] = values
    return data


def grouped_boxplot(
    left_data: dict[str, list[float]],
    right_data: dict[str, list[float]],
    *,
    left_label: str,
    right_label: str,
    ylabel: str,
    title: str,
    output_name: str,
    reference_lines: list[tuple[float, str, str]],
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    left_positions: list[float] = []
    right_positions: list[float] = []
    tick_positions: list[float] = []
    tick_labels: list[str] = []

    left_series: list[list[float]] = []
    right_series: list[list[float]] = []

    for index, profile in enumerate(PROFILE_ORDER):
        left_values = left_data.get(profile)
        right_values = right_data.get(profile)
        if not left_values and not right_values:
            continue

        base = index * 3.0 + 1.0
        left_positions.append(base)
        right_positions.append(base + 0.9)
        tick_positions.append(base + 0.45)
        tick_labels.append(profile_label(profile))
        left_series.append(left_values or [float("nan")])
        right_series.append(right_values or [float("nan")])

    if not left_series and not right_series:
        print(f"No data found for {output_name}; skipping.")
        return

    left_plot = ax.boxplot(
        left_series,
        positions=left_positions,
        widths=0.6,
        patch_artist=True,
        manage_ticks=False,
    )
    right_plot = ax.boxplot(
        right_series,
        positions=right_positions,
        widths=0.6,
        patch_artist=True,
        manage_ticks=False,
    )

    for patch in left_plot["boxes"]:
        patch.set(facecolor="#4C78A8", alpha=0.75)
    for patch in right_plot["boxes"]:
        patch.set(facecolor="#F58518", alpha=0.75)

    for value, label, style in reference_lines:
        ax.axhline(value, linestyle=style, linewidth=1.8, alpha=0.5, label=label)

    ax.plot([], [], color="#4C78A8", linewidth=10, alpha=0.75, label=left_label)
    ax.plot([], [], color="#F58518", linewidth=10, alpha=0.75, label=right_label)
    ax.set_xticks(tick_positions, tick_labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir() / output_name)
    plt.close(fig)


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
    grouped_boxplot(
        load_metric_runs(POSTGRES_INSERT_RUNS, "rows_per_sec"),
        load_metric_runs(POSTGRES_MINIO_INSERT_RUNS, "rows_per_sec"),
        left_label="PG (BYTEA)",
        right_label="PM (MinIO)",
        ylabel="Rows per Second",
        title="Insert Throughput Distribution by Resolution",
        output_name="boxplot_insert_throughput_runs.pdf",
        reference_lines=[
            (60.0, "60 fps", ":"),
            (30.0, "30 fps", "--"),
        ],
    )
    grouped_boxplot(
        load_metric_runs(POSTGRES_POINT_READ_RUNS, "latency_ms"),
        load_metric_runs(POSTGRES_MINIO_POINT_READ_RUNS, "latency_ms"),
        left_label="PG (BYTEA)",
        right_label="PM (MinIO)",
        ylabel="Latency (ms)",
        title="Binary Retrieval Latency Distribution by Resolution",
        output_name="boxplot_retrieval_latency_runs.pdf",
        reference_lines=[
            (1000 / 30, "30 fps budget (33.3 ms)", "--"),
            (1000 / 60, "60 fps budget (16.7 ms)", ":"),
        ],
    )

    summary_path = write_text_summary()
    print(f"Wrote aggregated text summary to {summary_path.name}")


if __name__ == "__main__":
    main()
