import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

matplotlib.rcParams.update({
    'font.size': 14,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12
})

RESULTS_DIR = "./results"
PROFILE_ORDER = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image", "6k_image"]
PROFILE_LABELS = ["1080p", "1440p", "4K", "5K", "6K"]

def load_summary_data(db_name, op_type, y_col_mean, y_col_std):
    data = {}
    for prof in PROFILE_ORDER:
        path = os.path.join(RESULTS_DIR, f"results_{db_name}_{op_type}_summary_{prof}.csv")
        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows:
                    continue
                last_row = rows[-1]
                if y_col_mean in last_row and last_row[y_col_mean]:
                    mean_val = float(last_row[y_col_mean])
                    std_val = float(last_row[y_col_std]) if y_col_std in last_row and last_row[y_col_std] else 0.0
                    if mean_val > 0.0:  # Skip 0.0 metrics from 6K timeouts etc if empty
                        data[prof] = (mean_val, std_val)
        except Exception:
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

# 1. Insert Throughput
pg_ins = load_summary_data("postgres", "insert", "mean_rows_per_sec", "std_rows_per_sec")
mg_ins = load_summary_data("mongo", "insert", "mean_rows_per_sec", "std_rows_per_sec")

labels_pg, pg_y, pg_std = extract_ordered_series(pg_ins)
labels_mg, mg_y, mg_std = extract_ordered_series(mg_ins)

plt.figure(figsize=(8, 5))
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

# 2. Retrieval Latency
pg_ret = load_summary_data("postgres", "retrieve", "mean_latency_ms", "std_latency_ms")
mg_ret = load_summary_data("mongo", "retrieve", "mean_latency_ms", "std_latency_ms")

labels_pg_ret, pgr_y, pgr_std = extract_ordered_series(pg_ret)
labels_mg_ret, mgr_y, mgr_std = extract_ordered_series(mg_ret)

plt.figure(figsize=(8, 5))
if pgr_y:
    plt.errorbar(labels_pg_ret, pgr_y, yerr=pgr_std, label="PostgreSQL", marker="o", capsize=5, lw=2.5, markersize=8)
if mgr_y:
    plt.errorbar(labels_mg_ret, mgr_y, yerr=mgr_std, label="MongoDB", marker="s", capsize=5, lw=2.5, markersize=8)

plt.title("Binary Retrieval Latency vs Image Resolution")
plt.xlabel("Image Resolution")
plt.ylabel("Latency (ms)")
plt.legend()
style_lineplot(plt.gca())
plt.tight_layout()
plt.savefig("../paper/figures/boxplot_retrieval_latency.pdf")
plt.close()

print("Linear plots with std dev generated successfully!")
