import csv
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({
    'font.size': 22,
    'axes.titlesize': 24,
    'axes.labelsize': 22,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'legend.fontsize': 16,
    'figure.titlesize': 24,
})

POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary"
POSTGRES_MINIO_INSERT_SUMMARY = "results_postgres_minio_insert_summary"

POSTGRES_RETRIEVAL_SUMMARY = "results_postgres_point_read_summary"
POSTGRES_MINIO_RETRIEVAL_SUMMARY = "results_postgres_minio_point_read_summary"

PROFILE_ORDER = ["480p_sd_image", "720p_hd_image", "1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image"]
PROFILE_LABELS = ["480p", "720p", "1080p", "1440p", "4K"]


def load_summary_data(stem, y_col_mean, y_col_std=None):
    data = {}
    for prof in PROFILE_ORDER:
        path = f"{stem}_{prof}.csv"
        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if not rows:
                    continue
                last_row = rows[-1]
                mean_val = float(last_row[y_col_mean])
                std_val = float(last_row[y_col_std]) if y_col_std and y_col_std in last_row else 0.0
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


# 1. Insert Throughput with frame-rate reference lines
pg_data = load_summary_data(POSTGRES_INSERT_SUMMARY, "mean_rows_per_sec", "std_rows_per_sec")
pm_data = load_summary_data(POSTGRES_MINIO_INSERT_SUMMARY, "mean_rows_per_sec", "std_rows_per_sec")

labels, pg_y, pg_std = extract_ordered_series(pg_data)
_, pm_y, pm_std = extract_ordered_series(pm_data)

plt.figure(figsize=(10, 6))
if pg_y:
    plt.errorbar(labels, pg_y, yerr=pg_std, label="PG (BYTEA)", marker="o", capsize=5, lw=2.5, markersize=9)
if pm_y:
    plt.errorbar(labels, pm_y, yerr=pm_std, label="PM (MinIO)", marker="^", capsize=5, lw=2.5, markersize=9)
# Frame-rate reference lines
plt.axhline(y=60, color='red', linestyle=':', linewidth=2.0, alpha=0.5, label='60 fps')
plt.axhline(y=30, color='orange', linestyle='--', linewidth=2.0, alpha=0.5, label='30 fps')
plt.title("Insert Throughput vs Image Resolution")
plt.xlabel("Image Resolution")
plt.ylabel("Rows per Second")
plt.legend()
style_lineplot(plt.gca())
plt.tight_layout()
plt.savefig("../paper/figures/boxplot_insert_throughput.pdf")
plt.close()

# 2. Retrieval Latency with frame-rate budget lines
pg_data = load_summary_data(POSTGRES_RETRIEVAL_SUMMARY, "mean_latency_ms", "std_latency_ms")
pm_data = load_summary_data(POSTGRES_MINIO_RETRIEVAL_SUMMARY, "mean_latency_ms", "std_latency_ms")

labels, pg_y, pg_std = extract_ordered_series(pg_data)
_, pm_y, pm_std = extract_ordered_series(pm_data)

plt.figure(figsize=(10, 6))
if pg_y:
    plt.errorbar(labels, pg_y, yerr=pg_std, label="PG (BYTEA)", marker="o", capsize=5, lw=2.5, markersize=9)
if pm_y:
    plt.errorbar(labels, pm_y, yerr=pm_std, label="PM (MinIO)", marker="^", capsize=5, lw=2.5, markersize=9)
# Frame-rate budget lines: at Nfps each frame has 1000/N ms
plt.axhline(y=1000/30, color='orange', linestyle='--', linewidth=2.0, alpha=0.5, label='30 fps budget (33.3 ms)')
plt.axhline(y=1000/60, color='red', linestyle=':', linewidth=2.0, alpha=0.5, label='60 fps budget (16.7 ms)')
plt.title("Binary Retrieval Latency vs Image Resolution")
plt.xlabel("Image Resolution")
plt.ylabel("Latency (ms)")
plt.legend()
style_lineplot(plt.gca())
plt.tight_layout()
plt.savefig("../paper/figures/boxplot_retrieval_latency.pdf")
plt.close()

print("Generated plots!")
