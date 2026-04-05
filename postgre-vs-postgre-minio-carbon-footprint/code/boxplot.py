import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

matplotlib.rcParams.update({
    'font.size': 20,
    'axes.titlesize': 22,
    'axes.labelsize': 20,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'legend.fontsize': 14,
    'figure.titlesize': 22,
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

# 1. Insert Throughput
pg_data = load_summary_data(POSTGRES_INSERT_SUMMARY, "mean_rows_per_sec", "std_rows_per_sec")
pm_data = load_summary_data(POSTGRES_MINIO_INSERT_SUMMARY, "mean_rows_per_sec", "std_rows_per_sec")

labels, pg_y, pg_std = extract_ordered_series(pg_data)
_, pm_y, pm_std = extract_ordered_series(pm_data)

plt.figure(figsize=(10, 6))
if pg_y:
    plt.errorbar(labels, pg_y, yerr=pg_std, label="PG (BYTEA)", marker="o", capsize=5, lw=2.5, markersize=9)
if pm_y:
    plt.errorbar(labels, pm_y, yerr=pm_std, label="PM (MinIO)", marker="^", capsize=5, lw=2.5, markersize=9)
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

# 2. Retrieval Latency
pg_data = load_summary_data(POSTGRES_RETRIEVAL_SUMMARY, "mean_latency_ms", "std_latency_ms")
pm_data = load_summary_data(POSTGRES_MINIO_RETRIEVAL_SUMMARY, "mean_latency_ms", "std_latency_ms")

labels, pg_y, pg_std = extract_ordered_series(pg_data)
_, pm_y, pm_std = extract_ordered_series(pm_data)

plt.figure(figsize=(10, 6))
if pg_y:
    plt.errorbar(labels, pg_y, yerr=pg_std, label="PG (BYTEA)", marker="o", capsize=5, lw=2.5, markersize=9)
if pm_y:
    plt.errorbar(labels, pm_y, yerr=pm_std, label="PM (MinIO)", marker="^", capsize=5, lw=2.5, markersize=9)
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

# 3. Carbon Footprint
carbon = {}
try:
    with open("emissions.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            carbon[row["project_name"]] = row
except Exception:
    pass

if "postgres_phase" in carbon and "postgres_minio_phase" in carbon:
    def profile_time(insert_stem, retrieve_stem, profile):
        t = 0.0
        try:
            with open(f"{insert_stem}_{profile}.csv", newline="") as f:
                row = list(csv.DictReader(f))[-1]
                t += float(row["mean_duration_sec"]) * float(row["n_runs"])
        except Exception:
            pass
        try:
            with open(f"{retrieve_stem}_{profile}.csv", newline="") as f:
                row = list(csv.DictReader(f))[-1]
                t += float(row["mean_latency_ms"]) * float(row["n_runs"]) / 1000.0
        except Exception:
            pass
        return t

    def per_resolution(phase_key, insert_stem, retrieve_stem):
        c = carbon[phase_key]
        total_dur   = float(c["duration"])
        energy_rate = float(c["energy_consumed"]) / total_dur   # kWh/s
        cpu_rate    = float(c["cpu_energy"])       / total_dur
        ram_rate    = float(c["ram_energy"])       / total_dur
        emis_rate   = float(c["emissions"])        / total_dur   # kg/s

        times = [profile_time(insert_stem, retrieve_stem, p) for p in PROFILE_ORDER]
        return {
            "times":     times,
            "energy":    [energy_rate * t * 1e6 for t in times],   # uWh
            "cpu":       [cpu_rate    * t * 1e6 for t in times],
            "ram":       [ram_rate    * t * 1e6 for t in times],
            "emissions": [emis_rate   * t * 1e6 for t in times],   # mg CO2eq
        }

    pg = per_resolution("postgres_phase", POSTGRES_INSERT_SUMMARY, POSTGRES_RETRIEVAL_SUMMARY)
    pm = per_resolution("postgres_minio_phase", POSTGRES_MINIO_INSERT_SUMMARY, POSTGRES_MINIO_RETRIEVAL_SUMMARY)

    # 3a. Single emissions plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(PROFILE_LABELS, pg["emissions"], marker="o", lw=2.5, markersize=9, label="PG (BYTEA)", color="#4C72B0")
    ax.plot(PROFILE_LABELS, pm["emissions"], marker="^", lw=2.5, markersize=9, label="PM (MinIO)", color="#55A868")
    ax.set_xlabel("Image Resolution")
    ax.set_ylabel("Estimated CO\u2082eq (mg)")
    ax.set_title("Estimated Carbon Emissions per Resolution")
    ax.legend()
    style_lineplot(ax)
    plt.tight_layout()
    plt.savefig("../paper/figures/carbon_footprint.pdf")
    plt.close()

    # 3b. Breakdown plots
    panels = [
        ("times",     "Duration (s)",           "Benchmark Duration"),
        ("energy",    "Energy (µWh)",            "Total Energy"),
        ("cpu",       "CPU Energy (µWh)",        "CPU Energy"),
        ("ram",       "RAM Energy (µWh)",        "RAM Energy"),
        ("emissions", "CO\u2082eq (mg)",          "Carbon Emissions"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes_flat = axes.flatten()

    for idx, (key, ylabel, title) in enumerate(panels):
        ax = axes_flat[idx]
        ax.plot(PROFILE_LABELS, pg[key], marker="o", lw=2.5, markersize=7, label="PG", color="#4C72B0")
        ax.plot(PROFILE_LABELS, pm[key], marker="^", lw=2.5, markersize=7, label="PM", color="#55A868")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        style_lineplot(ax)
        if idx == 4:
            ax.legend(loc="upper left")

    axes_flat[5].set_visible(False)
    plt.tight_layout()
    plt.savefig("../paper/figures/carbon_breakdown.pdf")
    plt.close()
    
    # Print tables for LaTeX
    print("--- LaTeX Tables for Paper ---")
    print("Carbon Breakdown Table:")
    for i, prof in enumerate(PROFILE_ORDER):
        print(f"{PROFILE_LABELS[i]} & {pg['times'][i]:.1f} & {pm['times'][i]:.1f} & "
              f"{pg['energy'][i]:.1f} & {pm['energy'][i]:.1f} & "
              f"{pg['cpu'][i]:.1f} & {pm['cpu'][i]:.1f} & "
              f"{pg['ram'][i]:.1f} & {pm['ram'][i]:.1f} & "
              f"{pg['emissions'][i]:.1f} & {pm['emissions'][i]:.1f} \\\\")
    
    total_pg_dur = sum(pg['times'])
    total_pm_dur = sum(pm['times'])
    total_pg_egy = sum(pg['energy'])
    total_pm_egy = sum(pm['energy'])
    total_pg_cpu = sum(pg['cpu'])
    total_pm_cpu = sum(pm['cpu'])
    total_pg_ram = sum(pg['ram'])
    total_pm_ram = sum(pm['ram'])
    total_pg_ems = sum(pg['emissions'])
    total_pm_ems = sum(pm['emissions'])
    print(f"Total & {total_pg_dur:.1f} & {total_pm_dur:.1f} & {total_pg_egy:.1f} & {total_pm_egy:.1f} & "
          f"{total_pg_cpu:.1f} & {total_pm_cpu:.1f} & {total_pg_ram:.1f} & {total_pm_ram:.1f} & "
          f"{total_pg_ems:.1f} & {total_pm_ems:.1f} \\\\")

print("Generated plots!")
