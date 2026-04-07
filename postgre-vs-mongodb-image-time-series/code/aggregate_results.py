import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Adjust plot styling for IEEE paper
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.2)
plt.rcParams.update({
    "font.family": "serif",
    "pdf.fonttype": 42,
    "ps.fonttype": 42
})

results_dir = Path("./results")
figures_dir = Path("../paper/figures")
figures_dir.mkdir(parents=True, exist_ok=True)

def parse_runs(db_name, op_type):
    pattern = f"results_{db_name}_{op_type}_runs_*.csv"
    dfs = []
    for fpath in results_dir.glob(pattern):
        profile = fpath.stem.replace(f"results_{db_name}_{op_type}_runs_", "")
        try:
            df = pd.read_csv(fpath)
            df['Database'] = 'PostgreSQL' if db_name == 'postgres' else 'MongoDB'
            df['Profile'] = profile
            dfs.append(df)
        except Exception as e:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

df_insert_pg = parse_runs('postgres', 'insert')
df_insert_mg = parse_runs('mongo', 'insert')
df_insert = pd.concat([df_insert_pg, df_insert_mg], ignore_index=True) if not df_insert_pg.empty or not df_insert_mg.empty else pd.DataFrame()

if not df_insert.empty:
    plt.figure(figsize=(7, 4.5))
    order = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image", "6k_image"]
    sns.boxplot(data=df_insert, x='Profile', y='rows_per_sec', hue='Database', order=[o for o in order if o in df_insert['Profile'].values])
    plt.title("Insert Throughput across Payload Resolutions")
    plt.ylabel("Throughput (rows/s)")
    plt.xlabel("Resolution Profile")
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.savefig(figures_dir / "boxplot_insert_throughput.pdf")
    plt.close()
    print("Generated boxplot_insert_throughput.pdf")

df_ret_pg = parse_runs('postgres', 'retrieve')
df_ret_mg = parse_runs('mongo', 'retrieve')
df_ret = pd.concat([df_ret_pg, df_ret_mg], ignore_index=True) if not df_ret_pg.empty or not df_ret_mg.empty else pd.DataFrame()

if not df_ret.empty:
    plt.figure(figsize=(7, 4.5))
    order = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image", "6k_image"]
    sns.boxplot(data=df_ret, x='Profile', y='latency_ms', hue='Database', order=[o for o in order if o in df_ret['Profile'].values])
    plt.title("Binary Retrieval Latency (100 rows)")
    plt.ylabel("Latency (ms)")
    plt.xlabel("Resolution Profile")
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.savefig(figures_dir / "boxplot_retrieval_latency.pdf")
    plt.close()
    print("Generated boxplot_retrieval_latency.pdf")

print("\n--- Summary Averages ---")
for profile in order:
    print(f"\nProfile: {profile}")
    for db in ['PostgreSQL', 'MongoDB']:
        if not df_insert.empty:
            sub = df_insert[(df_insert['Profile'] == profile) & (df_insert['Database'] == db)]
            if not sub.empty:
                print(f"  {db} Insert: {sub['rows_per_sec'].mean():.2f} rows/s | Amp: {sub['table_storage_amplification'].mean() if 'table_storage_amplification' in sub else 'N/A'}")
        if not df_ret.empty:
            sub_r = df_ret[(df_ret['Profile'] == profile) & (df_ret['Database'] == db)]
            if not sub_r.empty:
                print(f"  {db} Retrieve: {sub_r['latency_ms'].mean():.2f} ms")
