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


def main() -> None:
    plot_insert_throughput()
    plot_point_read_latency()
    print("Generated plots in paper/figures.")


if __name__ == "__main__":
    main()
