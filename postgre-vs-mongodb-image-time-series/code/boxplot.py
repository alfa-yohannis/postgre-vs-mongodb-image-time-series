import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# =========================
# GLOBAL FONT SETTINGS
# =========================
matplotlib.rcParams.update({
    'font.size': 14,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 13,
    'figure.titlesize': 16,
})

# =========================
# FILE PATHS
# =========================

POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary"
MONGO_INSERT_SUMMARY = "results_mongo_insert_summary"

POSTGRES_RET_SUMMARY = "results_postgres_retrieve_summary"
MONGO_RET_SUMMARY = "results_mongo_retrieve_summary"

# The x-axis order for our scaling plots
PROFILE_ORDER = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image", "6k_image"]
PROFILE_LABELS = ["1080p", "1440p", "4K", "5K", "6K"]

def load_summary_data(stem, y_col_mean, y_col_std=None):
    """
    Returns a dictionary mapping profile -> (mean, std)
    """
    data = {}
    for prof in PROFILE_ORDER:
        path = f"{stem}_{prof}.csv"
        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows: continue
                last_row = rows[-1]
                if y_col_mean in last_row:
                    mean_val = float(last_row[y_col_mean])
                    std_val = float(last_row[y_col_std]) if y_col_std and y_col_std in last_row else 0.0
                    data[prof] = (mean_val, std_val)
        except Exception as e:
            pass
    return data

def extract_ordered_series(data_dict):
    means = []
    stds = []
    valid_labels = []
    for i, prof in enumerate(PROFILE_ORDER):
        if prof in data_dict:
            means.append(data_dict[prof][0])
            stds.append(data_dict[prof][1])
            valid_labels.append(PROFILE_LABELS[i])
    return valid_labels, means, stds

def style_lineplot(ax):
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", pad=6)
    ax.tick_params(axis="y", pad=6)

# -----------------
# 1. Insert Throughput
# -----------------
pg_data = load_summary_data(POSTGRES_INSERT_SUMMARY, "mean_rows_per_sec", "std_rows_per_sec")
mg_data = load_summary_data(MONGO_INSERT_SUMMARY, "mean_rows_per_sec", "std_rows_per_sec")

labels_pg, pg_y, pg_std = extract_ordered_series(pg_data)

# Remove 6K from MongoDB since it silently failed
if "6k_image" in mg_data:
    del mg_data["6k_image"]

labels_mg, mg_y, mg_std = extract_ordered_series(mg_data)

plt.figure(figsize=(8, 4.5))
if pg_y:
    plt.errorbar(labels_pg, pg_y, yerr=pg_std, label="PostgreSQL", marker="o", capsize=5, lw=2.5, markersize=8)
if mg_y:
    plt.errorbar(labels_mg, mg_y, yerr=mg_std, label="MongoDB", marker="s", capsize=5, lw=2.5, markersize=8)
plt.title("Insert Throughput vs Image Resolution")
plt.xlabel("Image Resolution")
plt.ylabel("Rows per Second")
plt.legend()
style_lineplot(plt.gca())
plt.tight_layout()
plt.savefig("../paper/figures/boxplot_insert_throughput.pdf")
plt.close()

# -----------------
# 2. Binary Retrieval
# -----------------
pg_data = load_summary_data(POSTGRES_RET_SUMMARY, "mean_latency_ms", "std_latency_ms")
mg_data = load_summary_data(MONGO_RET_SUMMARY, "mean_latency_ms", "std_latency_ms")

labels_pg, pg_y, pg_std = extract_ordered_series(pg_data)

# Remove 6K from MongoDB since it silently failed
if "6k_image" in mg_data:
    del mg_data["6k_image"]

labels_mg, mg_y, mg_std = extract_ordered_series(mg_data)

plt.figure(figsize=(8, 4.5))
if pg_y:
    plt.errorbar(labels_pg, pg_y, yerr=pg_std, label="PostgreSQL", marker="o", capsize=5, lw=2.5, markersize=8)
if mg_y:
    plt.errorbar(labels_mg, mg_y, yerr=mg_std, label="MongoDB", marker="s", capsize=5, lw=2.5, markersize=8)
plt.title("Binary Retrieval Latency vs Image Resolution")
plt.xlabel("Image Resolution")
plt.ylabel("Latency (ms) for 100 rows")
plt.yscale("log")
plt.legend()
style_lineplot(plt.gca())
plt.tight_layout()
plt.savefig("../paper/figures/boxplot_retrieval_latency.pdf")
plt.close()

print("Generated plots!")
