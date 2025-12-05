import csv
import matplotlib.pyplot as plt


# =========================
# FILE PATHS
# =========================

POSTGRES_INSERT_RUNS = "results_postgres_insert_runs.csv"
MONGO_INSERT_RUNS = "results_mongo_insert_runs.csv"

POSTGRES_AGG_RUNS = "results_postgres_aggregate_runs.csv"
MONGO_AGG_RUNS = "results_mongo_aggregate_runs.csv"

POSTGRES_DRIVER_SUMMARY = "results_postgres_driver_summary.csv"
MONGO_DRIVER_SUMMARY = "results_mongo_driver_summary.csv"

POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary.csv"
MONGO_INSERT_SUMMARY = "results_mongo_insert_summary.csv"


# =========================
# CSV LOADERS
# =========================

def load_column_from_csv(path, column_name):
    values = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append(float(row[column_name]))
    return values


def load_single_value_from_summary(path, column_name):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            raise RuntimeError(f"No data in {path}")
        return float(rows[-1][column_name])


# =========================
# AXIS + BOXPLOT STYLE
# =========================

def style_boxplot(ax):
    # Horizontal grid only
    ax.grid(True, axis="y")

    # Show ONLY the x-axis line (bottom spine)
    ax.spines["bottom"].set_visible(True)
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Improve label spacing
    ax.tick_params(axis="x", pad=6)
    ax.tick_params(axis="y", pad=6)


# =========================
# 1) BOX PLOT: INSERT THROUGHPUT
# =========================

pg_insert_tp = load_column_from_csv(POSTGRES_INSERT_RUNS, "rows_per_sec")
mongo_insert_tp = load_column_from_csv(MONGO_INSERT_RUNS, "rows_per_sec")

plt.figure(figsize=(8, 4))
plt.boxplot(
    [pg_insert_tp, mongo_insert_tp],
    tick_labels=["PostgreSQL", "MongoDB"],
    widths=0.6,
    showmeans=True,
    meanprops=dict(marker="x", markeredgecolor="black", markersize=8)
)

plt.title("Insert Throughput (rows/sec)")
plt.ylabel("Rows per second")

style_boxplot(plt.gca())

plt.tight_layout(pad=0.4)
plt.savefig("boxplot_insert_throughput.pdf", bbox_inches="tight", pad_inches=0.05)
plt.close()


# =========================
# 2) BOX PLOT: AGGREGATION LATENCY
# =========================

pg_agg_lat = load_column_from_csv(POSTGRES_AGG_RUNS, "latency_ms")
mongo_agg_lat = load_column_from_csv(MONGO_AGG_RUNS, "latency_ms")

plt.figure(figsize=(8, 4))
plt.boxplot(
    [pg_agg_lat, mongo_agg_lat],
    tick_labels=["PostgreSQL", "MongoDB"],
    widths=0.6,
    showmeans=True,
    meanprops=dict(marker="x", markeredgecolor="black", markersize=8)
)

plt.title("Aggregation Latency (ms)")
plt.ylabel("Milliseconds")

style_boxplot(plt.gca())

plt.tight_layout(pad=0.4)
plt.savefig("boxplot_aggregation_latency.pdf", bbox_inches="tight", pad_inches=0.05)
plt.close()


# =========================
# 3) BOX PLOT: DRIVER ROUNDTRIP LATENCY
# =========================

pg_driver_lat = load_single_value_from_summary(
    POSTGRES_DRIVER_SUMMARY, "mean_latency_ms"
)
mongo_driver_lat = load_single_value_from_summary(
    MONGO_DRIVER_SUMMARY, "mean_latency_ms"
)

plt.figure(figsize=(8, 4))
plt.boxplot(
    [[pg_driver_lat], [mongo_driver_lat]],
    tick_labels=["PostgreSQL", "MongoDB"],
    widths=0.6,
    showmeans=True,
    meanprops=dict(marker="x", markeredgecolor="black", markersize=8)
)

plt.title("Driver Roundtrip Latency (ms)")
plt.ylabel("Milliseconds")

style_boxplot(plt.gca())

plt.tight_layout(pad=0.4)
plt.savefig("boxplot_driver_latency.pdf", bbox_inches="tight", pad_inches=0.05)
plt.close()


# =========================
# 4) STORAGE SIZE TABLE (PRINT ONLY)
# =========================

pg_table_mb = load_single_value_from_summary(
    POSTGRES_INSERT_SUMMARY, "mean_table_total_after_mb"
)
pg_db_mb = load_single_value_from_summary(
    POSTGRES_INSERT_SUMMARY, "mean_db_size_after_mb"
)

mongo_table_mb = load_single_value_from_summary(
    MONGO_INSERT_SUMMARY, "mean_table_total_after_mb"
)
mongo_db_mb = load_single_value_from_summary(
    MONGO_INSERT_SUMMARY, "mean_db_size_after_mb"
)

print("\n==============================")
print("STORAGE SIZE COMPARISON (MB)")
print("==============================")
print(f"{'Engine':<15} | {'Table/Collection':>18} | {'Database':>10}")
print("-" * 52)
print(f"{'PostgreSQL':<15} | {pg_table_mb:>18.2f} | {pg_db_mb:>10.2f}")
print(f"{'MongoDB':<15} | {mongo_table_mb:>18.2f} | {mongo_db_mb:>10.2f}")
print("==============================\n")

print("Generated PDF files:")
print(" - boxplot_insert_throughput.pdf")
print(" - boxplot_aggregation_latency.pdf")
print(" - boxplot_driver_latency.pdf")
