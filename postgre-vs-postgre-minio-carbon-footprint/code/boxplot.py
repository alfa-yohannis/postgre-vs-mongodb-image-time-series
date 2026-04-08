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

from carbon_utils import build_comparison_breakdown
from reporting_utils import (
    PROFILE_ORDER,
    load_last_rows_by_profile,
    profile_label,
    safe_float,
)


matplotlib.rcParams.update(
    {
        "font.size": 22,
        "axes.titlesize": 24,
        "axes.labelsize": 22,
        "xtick.labelsize": 20,
        "ytick.labelsize": 20,
        "legend.fontsize": 16,
        "figure.titlesize": 24,
    }
)

PG_COLOR = "#4C72B0"
PM_COLOR = "#55A868"
PG_LIGHT = "#A8C4E0"
PM_LIGHT = "#B7E0C1"

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


def extract_series(
    rows_by_profile: dict[str, dict[str, str]],
    profiles: list[str],
    mean_column: str,
    std_column: str,
) -> tuple[list[str], list[float], list[float]]:
    labels: list[str] = []
    means: list[float] = []
    stds: list[float] = []

    for profile in profiles:
        row = rows_by_profile.get(profile)
        mean_value = safe_float(row, mean_column)
        if mean_value is None:
            continue
        std_value = safe_float(row, std_column) or 0.0
        labels.append(profile_label(profile))
        means.append(mean_value)
        stds.append(std_value)

    return labels, means, stds


def style_axes(ax: plt.Axes) -> None:
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", pad=6)
    ax.tick_params(axis="y", pad=6)


def plot_insert_throughput() -> None:
    pg_rows = load_last_rows_by_profile(code_dir(), POSTGRES_INSERT_SUMMARY)
    pm_rows = load_last_rows_by_profile(code_dir(), POSTGRES_MINIO_INSERT_SUMMARY)
    profiles = [profile for profile in PROFILE_ORDER if profile in pg_rows or profile in pm_rows]

    labels, pg_means, pg_stds = extract_series(
        pg_rows,
        profiles,
        "mean_rows_per_sec",
        "std_rows_per_sec",
    )
    _, pm_means, pm_stds = extract_series(
        pm_rows,
        profiles,
        "mean_rows_per_sec",
        "std_rows_per_sec",
    )

    plt.figure(figsize=(10, 6))
    if pg_means:
        plt.errorbar(
            labels,
            pg_means,
            yerr=pg_stds,
            label="PG (BYTEA)",
            marker="o",
            capsize=5,
            lw=2.5,
            markersize=9,
            color=PG_COLOR,
        )
    if pm_means:
        plt.errorbar(
            labels,
            pm_means,
            yerr=pm_stds,
            label="PM (MinIO)",
            marker="^",
            capsize=5,
            lw=2.5,
            markersize=9,
            color=PM_COLOR,
        )

    plt.axhline(y=60, color="red", linestyle=":", linewidth=2.0, alpha=0.5, label="60 fps")
    plt.axhline(y=30, color="orange", linestyle="--", linewidth=2.0, alpha=0.5, label="30 fps")
    plt.title("Insert Throughput vs Image Resolution")
    plt.xlabel("Image Resolution")
    plt.ylabel("Rows per Second")
    plt.legend()
    style_axes(plt.gca())
    plt.tight_layout()
    plt.savefig(figures_dir() / "boxplot_insert_throughput.pdf")
    plt.close()


def plot_point_read_latency() -> None:
    pg_rows = load_last_rows_by_profile(code_dir(), POSTGRES_POINT_READ_SUMMARY)
    pm_rows = load_last_rows_by_profile(code_dir(), POSTGRES_MINIO_POINT_READ_SUMMARY)
    profiles = [profile for profile in PROFILE_ORDER if profile in pg_rows or profile in pm_rows]

    labels, pg_means, pg_stds = extract_series(
        pg_rows,
        profiles,
        "mean_latency_ms",
        "std_latency_ms",
    )
    _, pm_means, pm_stds = extract_series(
        pm_rows,
        profiles,
        "mean_latency_ms",
        "std_latency_ms",
    )

    plt.figure(figsize=(10, 6))
    if pg_means:
        plt.errorbar(
            labels,
            pg_means,
            yerr=pg_stds,
            label="PG (BYTEA)",
            marker="o",
            capsize=5,
            lw=2.5,
            markersize=9,
            color=PG_COLOR,
        )
    if pm_means:
        plt.errorbar(
            labels,
            pm_means,
            yerr=pm_stds,
            label="PM (MinIO)",
            marker="^",
            capsize=5,
            lw=2.5,
            markersize=9,
            color=PM_COLOR,
        )

    plt.axhline(
        y=1000 / 30,
        color="orange",
        linestyle="--",
        linewidth=2.0,
        alpha=0.5,
        label="30 fps budget (33.3 ms)",
    )
    plt.axhline(
        y=1000 / 60,
        color="red",
        linestyle=":",
        linewidth=2.0,
        alpha=0.5,
        label="60 fps budget (16.7 ms)",
    )
    plt.title("Binary Retrieval Latency vs Image Resolution")
    plt.xlabel("Image Resolution")
    plt.ylabel("Latency (ms)")
    plt.legend()
    style_axes(plt.gca())
    plt.tight_layout()
    plt.savefig(figures_dir() / "boxplot_retrieval_latency.pdf")
    plt.close()


def plot_carbon_footprint() -> None:
    rows = build_comparison_breakdown(code_dir())
    if not rows:
        print("No emissions data found; skipping carbon_footprint.pdf.")
        return

    labels = [str(row["profile_label"]) for row in rows]
    x_positions = list(range(len(rows)))
    width = 0.35
    pg_x = [x - width / 2 for x in x_positions]
    pm_x = [x + width / 2 for x in x_positions]

    pg_insert = [float(row["pg_insert_emissions_mg"]) for row in rows]
    pg_retrieval = [float(row.get("pg_retrieval_emissions_mg", row["pg_point_read_emissions_mg"])) for row in rows]
    pm_insert = [float(row["pm_insert_emissions_mg"]) for row in rows]
    pm_retrieval = [float(row.get("pm_retrieval_emissions_mg", row["pm_point_read_emissions_mg"])) for row in rows]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(
        pg_x,
        pg_insert,
        width,
        label="PostgreSQL — Insert",
        color=PG_COLOR,
        edgecolor=PG_COLOR,
        linewidth=0.8,
        zorder=3,
    )
    ax.bar(
        pg_x,
        pg_retrieval,
        width,
        label="PostgreSQL — Retrieval",
        bottom=pg_insert,
        color=PG_LIGHT,
        edgecolor=PG_COLOR,
        linewidth=0.8,
        hatch="//",
        zorder=3,
    )
    ax.bar(
        pm_x,
        pm_insert,
        width,
        label="PostgreSQL+MinIO — Insert",
        color=PM_COLOR,
        edgecolor=PM_COLOR,
        linewidth=0.8,
        zorder=3,
    )
    ax.bar(
        pm_x,
        pm_retrieval,
        width,
        label="PostgreSQL+MinIO — Retrieval",
        bottom=pm_insert,
        color=PM_LIGHT,
        edgecolor=PM_COLOR,
        linewidth=0.8,
        hatch="\\\\",
        zorder=3,
    )

    ax.plot(
        pg_x,
        [left + right for left, right in zip(pg_insert, pg_retrieval)],
        marker="o",
        lw=2.5,
        color=PG_COLOR,
        label="PostgreSQL — Total",
        zorder=5,
    )
    ax.plot(
        pm_x,
        [left + right for left, right in zip(pm_insert, pm_retrieval)],
        marker="^",
        lw=2.5,
        color=PM_COLOR,
        label="PostgreSQL+MinIO — Total",
        zorder=5,
    )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Image Resolution")
    ax.set_ylabel("Estimated CO2eq (mg)")
    ax.set_title("Carbon Emissions Contribution: Insert vs Retrieval")
    style_axes(ax)
    ax.legend(fontsize=11, loc="upper left")
    fig.tight_layout()

    fig.savefig(figures_dir() / "carbon_footprint.pdf")
    plt.close(fig)


def plot_carbon_breakdown() -> None:
    rows = build_comparison_breakdown(code_dir())
    if not rows:
        print("No emissions data found; skipping carbon_breakdown.pdf.")
        return

    labels = [str(row["profile_label"]) for row in rows]
    x_positions = list(range(len(rows)))
    width = 0.35
    pg_x = [x - width / 2 for x in x_positions]
    pm_x = [x + width / 2 for x in x_positions]

    pg_cpu = [float(row["pg_cpu_uwh"]) for row in rows]
    pg_ram = [float(row["pg_ram_uwh"]) for row in rows]
    pm_cpu = [float(row["pm_cpu_uwh"]) for row in rows]
    pm_ram = [float(row["pm_ram_uwh"]) for row in rows]
    pg_duration = [float(row["pg_duration_sec"]) for row in rows]
    pm_duration = [float(row["pm_duration_sec"]) for row in rows]

    fig, ax_energy = plt.subplots(figsize=(12, 6))
    ax_duration = ax_energy.twinx()

    ax_energy.bar(pg_x, pg_cpu, width, label="PG - CPU", color=PG_COLOR, zorder=3)
    ax_energy.bar(pg_x, pg_ram, width, label="PG - RAM", bottom=pg_cpu, color=PG_LIGHT, zorder=3)
    ax_energy.bar(pm_x, pm_cpu, width, label="PM - CPU", color=PM_COLOR, zorder=3)
    ax_energy.bar(pm_x, pm_ram, width, label="PM - RAM", bottom=pm_cpu, color=PM_LIGHT, zorder=3)

    ax_energy.plot(pg_x, [cpu + ram for cpu, ram in zip(pg_cpu, pg_ram)], marker="o", lw=2, color=PG_COLOR, label="PG - Total Energy", zorder=5)
    ax_energy.plot(pm_x, [cpu + ram for cpu, ram in zip(pm_cpu, pm_ram)], marker="^", lw=2, color=PM_COLOR, label="PM - Total Energy", zorder=5)

    ax_duration.plot(pg_x, pg_duration, lw=2.5, color=PG_COLOR, linestyle="--", label="PG - Duration", zorder=5)
    ax_duration.plot(pm_x, pm_duration, lw=2.5, color=PM_COLOR, linestyle="--", label="PM - Duration", zorder=5)

    ax_energy.set_xticks(x_positions)
    ax_energy.set_xticklabels(labels)
    ax_energy.set_xlabel("Image Resolution")
    ax_energy.set_ylabel("Energy (uWh)")
    ax_duration.set_ylabel("Duration (s)")
    ax_energy.set_title("Per-Resolution Energy Breakdown with Benchmark Duration")

    style_axes(ax_energy)
    ax_duration.spines["top"].set_visible(False)
    ax_duration.tick_params(axis="y", pad=6)

    handles_energy, labels_energy = ax_energy.get_legend_handles_labels()
    handles_duration, labels_duration = ax_duration.get_legend_handles_labels()
    ax_energy.legend(
        handles_energy + handles_duration,
        labels_energy + labels_duration,
        fontsize=11,
        loc="upper left",
    )

    fig.tight_layout()
    fig.savefig(figures_dir() / "carbon_breakdown.pdf")
    plt.close(fig)


def main() -> None:
    plot_insert_throughput()
    plot_point_read_latency()
    plot_carbon_footprint()
    plot_carbon_breakdown()
    print("Generated plots in paper/figures.")


if __name__ == "__main__":
    main()
