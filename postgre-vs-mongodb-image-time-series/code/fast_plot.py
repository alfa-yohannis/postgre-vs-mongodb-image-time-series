import csv
import os
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_clean"
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RESULTS_DIR = "./results"
PROFILE_ORDER = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image", "6k_image"]
PROFILE_LABELS = ["1080p", "1440p", "4K", "5K", "6K"]

def load_summary(db_name, op_type, y_col_mean, y_col_std):
    data = {}
    for prof in PROFILE_ORDER:
        if db_name == "mongo" and prof == "6k_image":
            continue
        path = os.path.join(RESULTS_DIR, f"results_{db_name}_{op_type}_summary_{prof}.csv")
        try:
            with open(path, newline="") as f:
                reader = list(csv.DictReader(f))
                if not reader: continue
                last_row = reader[-1]
                if y_col_mean in last_row and last_row[y_col_mean]:
                    mean_val = float(last_row[y_col_mean])
                    std_val = float(last_row[y_col_std]) if y_col_std in last_row and last_row[y_col_std] else 0.0
                    if mean_val > 0.0:
                        data[prof] = (mean_val, std_val)
        except:
            pass
    return data

def build_series(data_dict):
    m, s, l = [], [], []
    for i, prof in enumerate(PROFILE_ORDER):
        if prof in data_dict:
            m.append(data_dict[prof][0])
            s.append(data_dict[prof][1])
            l.append(PROFILE_LABELS[i])
    return l, m, s

pg_ins = load_summary("postgres", "insert", "mean_rows_per_sec", "std_rows_per_sec")
mg_ins = load_summary("mongo", "insert", "mean_rows_per_sec", "std_rows_per_sec")
l_pg, y_pg, s_pg = build_series(pg_ins)
l_mg, y_mg, s_mg = build_series(mg_ins)

plt.figure(figsize=(8, 5))
if y_pg: plt.errorbar(l_pg, y_pg, yerr=s_pg, label="PostgreSQL", marker="o", capsize=5, lw=2.5, markersize=8)
if y_mg: plt.errorbar(l_mg, y_mg, yerr=s_mg, label="MongoDB", marker="s", capsize=5, lw=2.5, markersize=8)
plt.title("Insert Throughput vs Image Resolution")
plt.xlabel("Image Resolution")
plt.ylabel("Rows per Second")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.7)
plt.savefig("../paper/figures/boxplot_insert_throughput.pdf")
plt.close()

pg_ret = load_summary("postgres", "retrieve", "mean_latency_ms", "std_latency_ms")
mg_ret = load_summary("mongo", "retrieve", "mean_latency_ms", "std_latency_ms")
l_pgr, yr_pg, sr_pg = build_series(pg_ret)
l_mgr, yr_mg, sr_mg = build_series(mg_ret)

plt.figure(figsize=(8, 5))
if yr_pg: plt.errorbar(l_pgr, yr_pg, yerr=sr_pg, label="PostgreSQL", marker="o", capsize=5, lw=2.5, markersize=8)
if yr_mg: plt.errorbar(l_mgr, yr_mg, yerr=sr_mg, label="MongoDB", marker="s", capsize=5, lw=2.5, markersize=8)
plt.title("Binary Retrieval Latency vs Image Resolution")
plt.xlabel("Image Resolution")
plt.ylabel("Latency (ms)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.7)
plt.savefig("../paper/figures/boxplot_retrieval_latency.pdf")
plt.close()

print("DONE")
