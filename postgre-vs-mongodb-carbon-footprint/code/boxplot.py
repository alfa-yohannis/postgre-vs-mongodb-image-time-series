import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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
# FILE PATHS (all relative to script location)
# =========================

RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
FIGURES_DIR = os.path.join(SCRIPT_DIR, "..", "paper", "figures")

def rpath(stem):
    return os.path.join(RESULTS_DIR, stem)

def fpath(name):
    return os.path.join(FIGURES_DIR, name)


POSTGRES_INSERT_SUMMARY = rpath("results_postgres_insert_summary")
MONGO_INSERT_SUMMARY    = rpath("results_mongo_insert_summary")
POSTGRES_RET_SUMMARY    = rpath("results_postgres_retrieve_summary")
MONGO_RET_SUMMARY       = rpath("results_mongo_retrieve_summary")

PROFILE_ORDER  = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image"]
PROFILE_LABELS = ["1080p", "1440p", "4K", "5K"]

PG_COLOR = "#4C72B0"
MG_COLOR = "#DD8452"


def load_summary_data(stem, y_col_mean, y_col_std=None):
    data = {}
    for prof in PROFILE_ORDER:
        path = f"{stem}_{prof}.csv"
        try:
            with open(path, newline="") as f:
                rows = list(csv.DictReader(f))
                if not rows:
                    continue
                last_row = rows[-1]
                if y_col_mean in last_row:
                    mean_val = float(last_row[y_col_mean])
                    std_val = (float(last_row[y_col_std])
                               if y_col_std and y_col_std in last_row else 0.0)
                    data[prof] = (mean_val, std_val)
        except Exception:
            pass
    return data


def extract_ordered_series(data_dict):
    means, stds, valid_labels = [], [], []
    for i, prof in enumerate(PROFILE_ORDER):
        if prof in data_dict:
            means.append(data_dict[prof][0])
            stds.append(data_dict[prof][1])
            valid_labels.append(PROFILE_LABELS[i])
    return valid_labels, means, stds


def style_ax(ax):
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", pad=6)
    ax.tick_params(axis="y", pad=6)


# -----------------
# 1. Insert Throughput
# -----------------
pg_data = load_summary_data(POSTGRES_INSERT_SUMMARY, "mean_rows_per_sec", "std_rows_per_sec")
mg_data = load_summary_data(MONGO_INSERT_SUMMARY,    "mean_rows_per_sec", "std_rows_per_sec")

labels_pg, pg_y, pg_std = extract_ordered_series(pg_data)
labels_mg, mg_y, mg_std = extract_ordered_series(mg_data)

fig, ax = plt.subplots(figsize=(8, 4.5))
if pg_y:
    ax.errorbar(labels_pg, pg_y, yerr=pg_std, label="PostgreSQL",
                marker="o", capsize=5, lw=2.5, markersize=8, color=PG_COLOR)
if mg_y:
    ax.errorbar(labels_mg, mg_y, yerr=mg_std, label="MongoDB",
                marker="s", capsize=5, lw=2.5, markersize=8, color=MG_COLOR)
ax.set_title("Insert Throughput vs Image Resolution")
ax.set_xlabel("Image Resolution")
ax.set_ylabel("Rows per Second")
ax.legend()
style_ax(ax)
plt.tight_layout()
plt.savefig(fpath("boxplot_insert_throughput.pdf"))
plt.close()

# -----------------
# 2. Binary Retrieval Latency
# -----------------
pg_data = load_summary_data(POSTGRES_RET_SUMMARY, "mean_latency_ms", "std_latency_ms")
mg_data = load_summary_data(MONGO_RET_SUMMARY,    "mean_latency_ms", "std_latency_ms")

labels_pg, pg_y, pg_std = extract_ordered_series(pg_data)
labels_mg, mg_y, mg_std = extract_ordered_series(mg_data)

fig, ax = plt.subplots(figsize=(8, 4.5))
if pg_y:
    ax.errorbar(labels_pg, pg_y, yerr=pg_std, label="PostgreSQL",
                marker="o", capsize=5, lw=2.5, markersize=8, color=PG_COLOR)
if mg_y:
    ax.errorbar(labels_mg, mg_y, yerr=mg_std, label="MongoDB",
                marker="s", capsize=5, lw=2.5, markersize=8, color=MG_COLOR)
ax.set_title("Binary Retrieval Latency vs Image Resolution")
ax.set_xlabel("Image Resolution")
ax.set_ylabel("Latency (ms) for 2,000 rows")
ax.legend()
style_ax(ax)
plt.tight_layout()
plt.savefig(fpath("boxplot_retrieval_latency.pdf"))
plt.close()

# -----------------
# 3. Carbon Footprint per Resolution
# -----------------
carbon = {}
try:
    with open(os.path.join(RESULTS_DIR, "emissions.csv"), newline="") as f:
        for row in csv.DictReader(f):
            carbon[row["project_name"]] = row
except Exception:
    pass

if "mongodb_phase" in carbon and "postgres_phase" in carbon:

    def insert_time(insert_stem, profile):
        try:
            with open(f"{insert_stem}_{profile}.csv", newline="") as f:
                row = list(csv.DictReader(f))[-1]
                return float(row["mean_duration_sec"]) * float(row["n_runs"])
        except Exception:
            return 0.0

    def retrieve_time(retrieve_stem, profile):
        try:
            with open(f"{retrieve_stem}_{profile}.csv", newline="") as f:
                row = list(csv.DictReader(f))[-1]
                return float(row["mean_latency_ms"]) * float(row["n_runs"]) / 1000.0
        except Exception:
            return 0.0

    def per_resolution(phase_key, insert_stem, retrieve_stem):
        c = carbon[phase_key]
        total_dur   = float(c["duration"])
        energy_rate = float(c["energy_consumed"]) / total_dur
        cpu_rate    = float(c["cpu_energy"])       / total_dur
        ram_rate    = float(c["ram_energy"])       / total_dur
        emis_rate   = float(c["emissions"])        / total_dur

        ins_times = [insert_time(insert_stem, p)    for p in PROFILE_ORDER]
        ret_times = [retrieve_time(retrieve_stem, p) for p in PROFILE_ORDER]
        tot_times = [i + r for i, r in zip(ins_times, ret_times)]
        return {
            "times":              tot_times,
            "energy":             [energy_rate * t * 1e6 for t in tot_times],
            "cpu":                [cpu_rate    * t * 1e6 for t in tot_times],
            "ram":                [ram_rate    * t * 1e6 for t in tot_times],
            "emissions":          [emis_rate   * t * 1e6 for t in tot_times],
            "insert_emissions":   [emis_rate   * t * 1e6 for t in ins_times],
            "retrieve_emissions": [emis_rate   * t * 1e6 for t in ret_times],
        }

    mg = per_resolution("mongodb_phase",  MONGO_INSERT_SUMMARY,    MONGO_RET_SUMMARY)
    pg = per_resolution("postgres_phase", POSTGRES_INSERT_SUMMARY, POSTGRES_RET_SUMMARY)

    # ── stacked bar: insert vs retrieval contribution ────────────────────
    x = list(range(len(PROFILE_LABELS)))
    width = 0.35
    pg_x = [xi - width / 2 for xi in x]
    mg_x = [xi + width / 2 for xi in x]

    INS_COLOR_PG  = PG_COLOR
    RET_COLOR_PG  = "#A8C4E0"   # lighter blue
    INS_COLOR_MG  = MG_COLOR
    RET_COLOR_MG  = "#F2C49B"   # lighter orange

    fig, ax = plt.subplots(figsize=(10, 5.5))

    # PostgreSQL bars
    ax.bar(pg_x, pg["insert_emissions"],   width, label="PostgreSQL — Insert",
           color=INS_COLOR_PG, zorder=3)
    ax.bar(pg_x, pg["retrieve_emissions"], width, label="PostgreSQL — Retrieval",
           bottom=pg["insert_emissions"], color=RET_COLOR_PG, zorder=3)

    # MongoDB bars
    ax.bar(mg_x, mg["insert_emissions"],   width, label="MongoDB — Insert",
           color=INS_COLOR_MG, zorder=3)
    ax.bar(mg_x, mg["retrieve_emissions"], width, label="MongoDB — Retrieval",
           bottom=mg["insert_emissions"], color=RET_COLOR_MG, zorder=3)

    # Lines connecting bar tops (total emissions)
    pg_totals = [i + r for i, r in zip(pg["insert_emissions"], pg["retrieve_emissions"])]
    mg_totals = [i + r for i, r in zip(mg["insert_emissions"], mg["retrieve_emissions"])]
    ax.plot(pg_x, pg_totals, marker="o", lw=2, markersize=7,
            color=PG_COLOR, zorder=5, label="PostgreSQL — Total")
    ax.plot(mg_x, mg_totals, marker="s", lw=2, markersize=7,
            color=MG_COLOR, zorder=5, label="MongoDB — Total")

    ax.set_xticks(x)
    ax.set_xticklabels(PROFILE_LABELS)
    ax.set_xlabel("Image Resolution")
    ax.set_ylabel("Estimated CO\u2082eq (mg)")
    ax.set_title("Carbon Emissions Contribution: Insert vs Retrieval")
    ax.legend(fontsize=11)
    style_ax(ax)
    plt.tight_layout()
    plt.savefig(fpath("carbon_footprint.pdf"))
    plt.close()

    # ── stacked energy bars (CPU+RAM) + duration secondary axis ──────────
    CPU_COLOR_PG = PG_COLOR
    RAM_COLOR_PG = "#A8C4E0"
    CPU_COLOR_MG = MG_COLOR
    RAM_COLOR_MG = "#F2C49B"

    fig, ax_e = plt.subplots(figsize=(11, 5.5))
    ax_d = ax_e.twinx()

    # Stacked bars: CPU (bottom) + RAM (top)
    ax_e.bar(pg_x, pg["cpu"], width, label="PostgreSQL — CPU",
             color=CPU_COLOR_PG, zorder=3)
    ax_e.bar(pg_x, pg["ram"], width, label="PostgreSQL — RAM",
             bottom=pg["cpu"], color=RAM_COLOR_PG, zorder=3)
    ax_e.bar(mg_x, mg["cpu"], width, label="MongoDB — CPU",
             color=CPU_COLOR_MG, zorder=3)
    ax_e.bar(mg_x, mg["ram"], width, label="MongoDB — RAM",
             bottom=mg["cpu"], color=RAM_COLOR_MG, zorder=3)

    # Lines connecting bar tops (total energy)
    pg_energy_totals = [c + r for c, r in zip(pg["cpu"], pg["ram"])]
    mg_energy_totals = [c + r for c, r in zip(mg["cpu"], mg["ram"])]
    ax_e.plot(pg_x, pg_energy_totals, marker="o", lw=2, markersize=7,
              color=CPU_COLOR_PG, zorder=5, label="PostgreSQL — Total Energy")
    ax_e.plot(mg_x, mg_energy_totals, marker="s", lw=2, markersize=7,
              color=CPU_COLOR_MG, zorder=5, label="MongoDB — Total Energy")

    # Duration lines on secondary axis (dashed, no markers)
    ax_d.plot(pg_x, pg["times"], lw=2.5, color=CPU_COLOR_PG,
              linestyle="--", zorder=5, label="PostgreSQL — Duration")
    ax_d.plot(mg_x, mg["times"], lw=2.5, color=CPU_COLOR_MG,
              linestyle="--", zorder=5, label="MongoDB — Duration")

    ax_e.set_xticks(x)
    ax_e.set_xticklabels(PROFILE_LABELS)
    ax_e.set_xlabel("Image Resolution")
    ax_e.set_ylabel("Energy (µWh)")
    ax_d.set_ylabel("Duration (s)")
    ax_e.set_title("Per-Resolution Energy Breakdown with Benchmark Duration")

    # Combined legend from both axes
    handles_e, labels_e = ax_e.get_legend_handles_labels()
    handles_d, labels_d = ax_d.get_legend_handles_labels()
    ax_e.legend(handles_e + handles_d, labels_e + labels_d,
                fontsize=10, loc="upper left")

    style_ax(ax_e)
    ax_d.spines["top"].set_visible(False)
    ax_d.tick_params(axis="y", pad=6)

    plt.tight_layout()
    plt.savefig(fpath("carbon_breakdown.pdf"))
    plt.close()

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
