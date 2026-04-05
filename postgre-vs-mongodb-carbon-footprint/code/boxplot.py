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
PROFILE_ORDER = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image"]
PROFILE_LABELS = ["1080p", "1440p", "4K", "5K"]

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

# -----------------
# 3. Carbon Footprint per Resolution
#    Estimated via power-rate × profile time
#    power_rate = total_metric / total_duration  (constant-power assumption)
# -----------------
carbon = {}
try:
    with open("emissions.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            carbon[row["project_name"]] = row
except Exception:
    pass

if "mongodb_phase" in carbon and "postgres_phase" in carbon:

    def profile_time(insert_stem, retrieve_stem, profile):
        """Sum of (n_runs × mean_duration) for insert + retrieve (seconds)."""
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
        """Return dict of lists: duration_s, energy_uwh, cpu_uwh, ram_uwh, emissions_ug per profile."""
        c = carbon[phase_key]
        total_dur   = float(c["duration"])
        energy_rate = float(c["energy_consumed"]) / total_dur   # kWh/s
        cpu_rate    = float(c["cpu_energy"])       / total_dur
        ram_rate    = float(c["ram_energy"])       / total_dur
        emis_rate   = float(c["emissions"])        / total_dur   # kg/s

        times = [profile_time(insert_stem, retrieve_stem, p) for p in PROFILE_ORDER]
        return {
            "times":     times,
            "energy":    [energy_rate * t * 1e6 for t in times],   # µWh
            "cpu":       [cpu_rate    * t * 1e6 for t in times],
            "ram":       [ram_rate    * t * 1e6 for t in times],
            "emissions": [emis_rate   * t * 1e6 for t in times],   # kg/s × s × 1e6 = mg CO₂eq
        }

    # kg CO₂ × 1e9 = µg CO₂  (1 kg = 1e9 µg)
    # actually 1 kg = 1e6 mg = 1e9 µg — correct

    mg = per_resolution("mongodb_phase",  MONGO_INSERT_SUMMARY,    MONGO_RET_SUMMARY)
    pg = per_resolution("postgres_phase", POSTGRES_INSERT_SUMMARY, POSTGRES_RET_SUMMARY)

    # ── single summary line chart (existing figure) ──────────────────────
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(PROFILE_LABELS, pg["emissions"], marker="o", lw=2.5, markersize=8,
            label="PostgreSQL", color="#4C72B0")
    ax.plot(PROFILE_LABELS, mg["emissions"], marker="s", lw=2.5, markersize=8,
            label="MongoDB", color="#DD8452")
    ax.set_xlabel("Image Resolution")
    ax.set_ylabel("Estimated CO\u2082eq (mg)")
    ax.set_title("Estimated Carbon Emissions per Resolution")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig("../paper/figures/carbon_footprint.pdf")
    plt.close()

    # ── 4-panel breakdown line chart ─────────────────────────────────────
    panels = [
        ("times",     "Duration (s)",           "Benchmark Duration"),
        ("energy",    "Energy (µWh)",            "Total Energy"),
        ("cpu",       "CPU Energy (µWh)",        "CPU Energy"),
        ("ram",       "RAM Energy (µWh)",        "RAM Energy"),
        ("emissions", "CO\u2082eq (mg)",          "Carbon Emissions"),
    ]
    # Use a 2×3 grid but only fill 5 cells; hide the 6th
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    axes_flat = axes.flatten()

    for idx, (key, ylabel, title) in enumerate(panels):
        ax = axes_flat[idx]
        ax.plot(PROFILE_LABELS, pg[key], marker="o", lw=2.5, markersize=7,
                label="PostgreSQL", color="#4C72B0")
        ax.plot(PROFILE_LABELS, mg[key], marker="s", lw=2.5, markersize=7,
                label="MongoDB",    color="#DD8452")
        ax.set_title(title)
        ax.set_xlabel("Resolution")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    axes_flat[-1].set_visible(False)   # hide empty 6th cell
    plt.suptitle("Per-Resolution Carbon Footprint Breakdown", fontsize=15, y=1.01)
    plt.tight_layout()
    plt.savefig("../paper/figures/carbon_breakdown.pdf", bbox_inches="tight")
    plt.close()

    # ── print per-resolution table values (for paper) ─────────────────────
    print("\nPer-resolution carbon breakdown:")
    print(f"{'Res':<8} {'PG_dur':>8} {'MG_dur':>8} {'PG_E':>9} {'MG_E':>9} "
          f"{'PG_cpu':>9} {'MG_cpu':>9} {'PG_ram':>9} {'MG_ram':>9} "
          f"{'PG_co2(mg)':>12} {'MG_co2(mg)':>12}")
    for i, lbl in enumerate(PROFILE_LABELS):
        print(f"{lbl:<8} {pg['times'][i]:>8.1f} {mg['times'][i]:>8.1f} "
              f"{pg['energy'][i]:>9.1f} {mg['energy'][i]:>9.1f} "
              f"{pg['cpu'][i]:>9.2f} {mg['cpu'][i]:>9.2f} "
              f"{pg['ram'][i]:>9.1f} {mg['ram'][i]:>9.1f} "
              f"{pg['emissions'][i]:>12.2f} {mg['emissions'][i]:>12.2f}")

print("Generated plots!")
